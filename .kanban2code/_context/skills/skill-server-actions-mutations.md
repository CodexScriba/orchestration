---
skill_name: skill-server-actions-mutations
version: "16.0.10"
framework: Next.js
react_version: "19"
last_verified: "2025-12-18"
always_attach: false
priority: 8
triggers:
  - server action
  - use server
  - useActionState
  - useFormState
  - form action
  - FormData
  - mutation
  - submit
  - zod
  - validation
---

<!--
LLM INSTRUCTION: Apply when user creates forms or server-side mutations.
SECURITY: Server Actions are PUBLIC HTTP endpoints. ALWAYS validate with Zod.
REACT 19 CHANGE: useFormState is RENAMED to useActionState. Import from 'react' not 'react-dom'.
CRITICAL: redirect() throws an error intentionally - NEVER catch it in try/catch.
Use .bind() for passing IDs, NOT hidden inputs (which are tamperable).
-->

# Server Actions & Mutations

> **Target:** Next.js 16.0.10 | **React:** 19 | **Last Verified:** 2025-12-18

## 1. What AI Models Get Wrong

- **Using `useFormState` from 'react-dom'** → LLMs use React 18 import. React 19 renames to `useActionState` from 'react'.
- **Skipping Zod validation** → LLMs trust FormData directly. Server Actions are public endpoints—validation is mandatory.
- **Placing `redirect()` inside try/catch** → LLMs catch the redirect error. redirect() throws intentionally and must not be caught.
- **Defining actions in 'use client' files** → LLMs put 'use server' inside client components. Actions must be in server files.
- **Using hidden inputs for IDs** → LLMs use `<input type="hidden">` for passing IDs. Use `.bind()` for secure argument passing.

## 2. Golden Rules

### ✅ DO
- **Validate ALL input with Zod** → Server Actions are public HTTP endpoints
- **Use `useActionState` from 'react'** → React 19's renamed hook with isPending
- **Use `.bind()` for secure argument passing** → Prevents client tampering
- **Place `redirect()` outside try/catch** → It throws to trigger navigation
- **Call `revalidateTag()` after mutations** → Update cached data

### ❌ DON'T  
- **Don't trust FormData** → Always validate server-side
- **Don't use `useFormState`** → Renamed to useActionState in React 19
- **Don't catch redirect/notFound errors** → They throw intentionally
- **Don't define 'use server' in 'use client' files** → Invalid, actions must be separate
- **Don't use hidden inputs for sensitive IDs** → Use .bind() instead

## 3. Critical Patterns

### Secure Server Action with Zod

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
'use server';

export async function createUser(formData: FormData) {
  // Trusting raw FormData - SECURITY RISK
  const email = formData.get('email') as string;
  const role = formData.get('role') as string;
  
  await db.user.create({ email, role }); // No validation!
}
```

**✅ CORRECT (v16):**
```typescript
'use server';

import { z } from 'zod';
import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';

const schema = z.object({
  email: z.string().email(),
  role: z.enum(['user', 'admin']),
});

type CreateUserState =
  | {
      error: string;
      issues?: Record<string, string[]>;
    }
  | null;

export async function createUser(_prevState: CreateUserState, formData: FormData): Promise<CreateUserState> {
  // 1. Authentication
  const session = await auth();
  if (!session?.user) {
    return { error: 'Unauthorized' };
  }

  // 2. Validation (MANDATORY)
  const parsed = schema.safeParse({
    email: formData.get('email'),
    role: formData.get('role'),
  });

  if (!parsed.success) {
    return { error: 'Invalid input', issues: parsed.error.flatten().fieldErrors };
  }

  // 3. Mutation
  try {
    await db.user.create({ data: parsed.data });
  } catch (e) {
    return { error: 'Database error' };
  }

  // 4. Redirect (OUTSIDE try/catch)
  redirect('/users');
}
```
**Why:** Server Actions are public endpoints. Zod validation is non-negotiable security.

---

### useActionState (React 19)

**❌ WRONG (v14/React 18 - Hallucination Risk):**
```typescript
'use client';
import { useFormState } from 'react-dom'; // WRONG import

export function UserForm() {
  const [state, action] = useFormState(createUser, null); // Missing isPending
  
  return <form action={action}>...</form>;
}
```

**✅ CORRECT (v16/React 19):**
```typescript
'use client';
import { useActionState } from 'react'; // Correct import
import { createUser } from './actions';

export function UserForm() {
  // React 19: [state, dispatch, isPending]
  const [state, formAction, isPending] = useActionState(createUser, null);

  return (
    <form action={formAction}>
      <input name="email" type="email" required />
      
      {state?.issues?.email && (
        <span className="error">{state.issues.email}</span>
      )}
      
      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create User'}
      </button>
      
      {state?.error && <div className="error">{state.error}</div>}
    </form>
  );
}
```
**Why:** React 19 renamed useFormState to useActionState and added isPending as third return value.

---

### Secure Argument Binding

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Hidden inputs can be tampered with in DevTools
export function DeleteButton({ userId }: { userId: string }) {
  return (
    <form action={deleteUser}>
      <input type="hidden" name="userId" value={userId} /> {/* Tamperable! */}
      <button>Delete</button>
    </form>
  );
}
```

**✅ CORRECT (v16):**
```typescript
// Server Component - .bind() is secure
export function DeleteButton({ userId }: { userId: string }) {
  const deleteUserWithId = deleteUser.bind(null, userId);
  
  return (
    <form action={deleteUserWithId}>
      <button>Delete</button>
    </form>
  );
}

// actions.ts
'use server';
export async function deleteUser(userId: string, formData: FormData) {
  // userId is bound server-side, client cannot tamper
  await db.user.delete({ where: { id: userId } });
  revalidateTag('users');
}
```
**Why:** .bind() serializes arguments in the React Server Components closure, not in client HTML.

---

### Redirect Outside Try/Catch

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
'use server';

export async function submitForm(formData: FormData) {
  try {
    await db.insert(formData);
    redirect('/success'); // CAUGHT by catch block!
  } catch (e) {
    return { error: 'Failed' }; // Redirect never happens
  }
}
```

**✅ CORRECT (v16):**
```typescript
'use server';
import { redirect } from 'next/navigation';

export async function submitForm(formData: FormData) {
  let success = false;
  
  try {
    await db.insert(formData);
    success = true;
  } catch (e) {
    return { error: 'Database error' };
  }

  // Redirect OUTSIDE try/catch
  if (success) {
    redirect('/success');
  }
}
```
**Why:** redirect() throws a NEXT_REDIRECT error to trigger navigation. Catching it prevents the redirect.

---

### useFormStatus for Submit Buttons

**❌ WRONG (v14/v15 - Hallucination Risk):**
```typescript
// Prop drilling isPending to button
export function Form({ isPending }: { isPending: boolean }) {
  return (
    <form>
      <SubmitButton disabled={isPending} />
    </form>
  );
}
```

**✅ CORRECT (v16/React 19):**
```typescript
'use client';
import { useFormStatus } from 'react-dom';

export function SubmitButton() {
  const { pending, data, method, action } = useFormStatus();
  
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Submitting...' : 'Submit'}
    </button>
  );
}

// Usage - no prop drilling needed
export function Form() {
  return (
    <form action={submitAction}>
      <input name="email" />
      <SubmitButton /> {/* Reads pending from parent form */}
    </form>
  );
}
```
**Why:** useFormStatus reads status from the nearest parent form without prop drilling.

## 4. Quick Reference Table

| Feature | ❌ Don't | ✅ Do |
|---------|---------|------|
| Form Hook | `useFormState` from 'react-dom' | `useActionState` from 'react' |
| Validation | Trust raw FormData | Validate with Zod (mandatory) |
| Pass IDs | `<input type="hidden">` | `.bind(null, id)` |
| Redirect | Inside try/catch | Outside try/catch block |
| Action Files | 'use server' in 'use client' file | Separate actions.ts file |
| Button State | Prop drilling isPending | `useFormStatus` hook |
| After Mutation | Forget cache | `revalidateTag()` or `router.refresh()` |

## 5. Checklist Before Coding

- [ ] Server Action file has `'use server'` at top (not inside 'use client' file)
- [ ] All input validated with Zod before any database operations
- [ ] Using `useActionState` from 'react' (not useFormState from 'react-dom')
- [ ] `redirect()` and `notFound()` calls are outside try/catch blocks
- [ ] Using `.bind()` for passing IDs instead of hidden inputs
- [ ] Calling `revalidateTag()` or `router.refresh()` after mutations

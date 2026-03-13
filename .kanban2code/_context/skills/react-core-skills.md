---
skill_name: react-core-skills
version: "19.0.0"
framework: React
typescript_version: "5.x"
last_verified: "2025-12-18"
always_attach: true
priority: 9
triggers:
  - react
  - tsx
  - jsx
  - component
  - hooks
  - usestate
  - useeffect
  - typescript
---

<!--
LLM INSTRUCTION: This is a CORE skill file for React + TypeScript projects.
ALWAYS apply these rules when generating React/TypeScript code.
Your training data contains mixed conventions - ENFORCE consistent naming below.
Key focus: Naming consistency, component patterns, TypeScript safety, hooks best practices.
When you see WRONG, that's inconsistent/bad practice. Use CORRECT instead.
-->

# React + TypeScript Core Skills

> **Target:** React 19+ | **TypeScript:** 5.x | **Last Verified:** 2025-12-18

## 1. What AI Models Get Wrong

- **Inconsistent file naming** → LLMs randomly switch between `UserProfile.tsx`, `user-profile.tsx`, `user_profile.tsx` in the same project. Pick ONE convention and stick to it.
- **Mixed variable naming** → LLMs use `userName`, `user_name`, `UserName` interchangeably. TypeScript/React uses camelCase for variables.
- **Prop interfaces without suffix** → LLMs create `interface User` when it should be `UserProps` to distinguish from data types.
- **Default exports without component name** → LLMs write `export default function() {}` losing type information.
- **Using `any` type** → LLMs default to `any` when types are unclear. Always use proper types or `unknown`.
- **Hooks outside components** → LLMs call hooks in helper functions or conditionally.
- **Missing key prop** → LLMs forget `key` in `.map()` causing React warnings.

## 2. Naming Convention Rules

### File Naming

| Type | Convention | Example |
|------|-----------|---------|
| Components | `PascalCase.tsx` | `TaskCard.tsx`, `UserProfile.tsx` |
| Hooks | `useCamelCase.ts` | `useTaskData.ts`, `useKeyboard.ts` |
| Services/Utils | `kebab-case.ts` | `task-service.ts`, `date-utils.ts` |
| Types | `kebab-case.ts` or `PascalCase.ts` | `task.ts`, `filters.ts` |
| Constants | `kebab-case.ts` | `constants.ts`, `api-endpoints.ts` |

### Code Naming

| Type | Convention | Example |
|------|-----------|---------|
| Components | `PascalCase` | `TaskCard`, `UserProfile` |
| Props interfaces | `{Component}Props` | `TaskCardProps`, `UserProfileProps` |
| Hooks | `useCamelCase` | `useTaskData()`, `useLocalStorage()` |
| Variables | `camelCase` | `filteredTasks`, `isLoading` |
| Functions | `camelCase` | `handleClick`, `formatDate` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_ITEMS`, `API_URL` |
| Types/Interfaces | `PascalCase` | `Task`, `User`, `FilterState` |
| Enums | `PascalCase` | `Status`, `Priority` |
| CSS classes | `kebab-case` | `task-card`, `btn-primary` |

## 3. Golden Rules

### DO
- **Component files: PascalCase.tsx** → `TaskCard.tsx`, `UserProfile.tsx`
- **Props interfaces: {Component}Props** → `interface TaskCardProps`
- **Hooks: use + PascalCase** → `useTaskData`, `useKeyboard`
- **Variables/functions: camelCase** → `filteredTasks`, `handleClick`
- **Constants: UPPER_SNAKE_CASE** → `MAX_ITEMS`, `DEFAULT_TIMEOUT`
- **CSS classes: kebab-case** → `task-card`, `user-profile`
- **One component per file** → File exports single component matching filename
- **Type all props and state** → No implicit `any`
- **Hooks at top level** → Never conditional, never in loops

### DON'T
- **Don't mix naming conventions** → No `user-profile.tsx` and `UserSettings.tsx` together
- **Don't use `any` type** → Use `unknown` or define proper types
- **Don't call hooks conditionally** → No `if (x) { useState() }`
- **Don't mutate state directly** → Use setState, never `state.x = y`
- **Don't use index as key** → Use `key={item.id}` not `key={index}`

## 4. Critical Patterns

### File and Component Naming

**WRONG (Inconsistent):**
```typescript
// Mixed conventions in same project
user-profile.tsx          // kebab-case
TaskCard.tsx             // PascalCase
user_settings.tsx        // snake_case

export default function() { ... }  // Anonymous
```

**CORRECT (Consistent):**
```typescript
// All components: PascalCase.tsx
UserProfile.tsx
TaskCard.tsx
UserSettings.tsx

// File: UserProfile.tsx
interface UserProfileProps {
  userId: string;
  onUpdate: (user: User) => void;
}

export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  return <div>...</div>;
}
```

---

### Variable and Function Naming

**WRONG (Inconsistent):**
```typescript
const UserName = 'John';        // PascalCase (wrong)
const user_email = 'john@...';  // snake_case (wrong)
const HandleClick = () => {};   // PascalCase (wrong)
```

**CORRECT (Consistent):**
```typescript
const userName = 'John';           // camelCase
const userEmail = 'john@...';      // camelCase
const handleClick = () => {};      // camelCase

const MAX_RETRIES = 3;             // UPPER_SNAKE_CASE for constants
const DEFAULT_TIMEOUT = 5000;
```

---

### Props Interface Naming

**WRONG (Ambiguous):**
```typescript
interface Task {  // Is this data or props?
  onComplete: () => void;
}

function TaskCard(props: any) {  // No type safety
  return <div>{props.task.title}</div>;
}
```

**CORRECT (Clear):**
```typescript
// Data type
interface Task {
  id: string;
  title: string;
}

// Props type (suffix: Props)
interface TaskCardProps {
  task: Task;
  onComplete: (id: string) => void;
}

function TaskCard({ task, onComplete }: TaskCardProps) {
  return <div>{task.title}</div>;
}
```

---

### Hook Naming and Usage

**WRONG:**
```typescript
function taskData() {  // Missing 'use' prefix
  return useState([]);
}

function TaskList() {
  if (condition) {
    const [data] = useState([]);  // Conditional hook!
  }
}
```

**CORRECT:**
```typescript
export function useTaskData() {  // use + PascalCase
  const [data, setData] = useState<Task[]>([]);
  return { data, setData };
}

function TaskList() {
  const [data] = useState<Task[]>([]);  // Top level
  if (!data) return null;  // Conditional RENDER, not hook
  return <div>...</div>;
}
```

---

### CSS Class Naming

**WRONG (Inconsistent):**
```typescript
<div className="TaskCard">        // PascalCase
<div className="task_card">       // snake_case
<div className="taskcard">        // no separator
```

**CORRECT (Consistent):**
```typescript
<div className="task-card">           // kebab-case
  <h2 className="task-card-title">    // kebab-case
  <div className="task-card-actions"> // kebab-case
```

## 5. Component Structure Template

```typescript
// File: TaskCard.tsx
import { useState } from 'react';
import type { Task } from '@/types/task';
import './TaskCard.css';

// Constants
const MAX_TITLE_LENGTH = 100;

// Props interface
interface TaskCardProps {
  task: Task;
  onEdit?: (task: Task) => void;
  onDelete?: (id: string) => void;
}

// Component
export function TaskCard({ task, onEdit, onDelete }: TaskCardProps) {
  // Hooks at top
  const [isExpanded, setIsExpanded] = useState(false);

  // Handlers
  const handleEdit = () => onEdit?.(task);
  const handleDelete = () => onDelete?.(task.id);

  // Early returns
  if (!task) return null;

  // Render
  return (
    <div className="task-card">
      <h3 className="task-card-title">{task.title}</h3>
      <div className="task-card-actions">
        <button onClick={handleEdit}>Edit</button>
        <button onClick={handleDelete}>Delete</button>
      </div>
    </div>
  );
}
```

## 6. Quick Reference Table

| Category | Convention | Examples |
|----------|-----------|----------|
| **Component files** | `PascalCase.tsx` | `TaskCard.tsx`, `UserProfile.tsx` |
| **Component names** | `PascalCase` | `TaskCard`, `UserProfile` |
| **Props interfaces** | `{Component}Props` | `TaskCardProps`, `UserProfileProps` |
| **Hook files** | `useCamelCase.ts` | `useTaskData.ts`, `useKeyboard.ts` |
| **Hook functions** | `useCamelCase` | `useTaskData()`, `useLocalStorage()` |
| **Variables** | `camelCase` | `filteredTasks`, `isLoading` |
| **Functions** | `camelCase` | `handleClick`, `formatDate` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_ITEMS`, `API_URL` |
| **Types/Interfaces** | `PascalCase` | `Task`, `User`, `FilterState` |
| **CSS classes** | `kebab-case` | `task-card`, `btn-primary` |
| **Service files** | `kebab-case.ts` | `task-service.ts`, `date-utils.ts` |

## 7. Checklist Before Coding

- [ ] Component files use PascalCase.tsx
- [ ] Component names match filename
- [ ] Props have {Component}Props interface
- [ ] Hooks use 'use' prefix, called at top level
- [ ] Variables use camelCase, constants use UPPER_SNAKE_CASE
- [ ] CSS classes use kebab-case
- [ ] No `any` types
- [ ] List items have unique `key` prop (not index)
- [ ] Event handlers are typed (React.MouseEvent, etc.)

## 8. Common Mistakes

```typescript
// WRONG: index as key
{tasks.map((task, i) => <TaskCard key={i} />)}

// CORRECT: unique ID
{tasks.map((task) => <TaskCard key={task.id} />)}
```

```typescript
// WRONG: state mutation
items.push(newItem);

// CORRECT: immutable update
setItems([...items, newItem]);
```

```typescript
// WRONG: conditional hook
if (show) { const [x] = useState(); }

// CORRECT: conditional render
const [x] = useState();
if (!show) return null;
```

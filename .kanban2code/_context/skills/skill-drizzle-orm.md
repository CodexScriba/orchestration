---
skill_name: skill-drizzle-orm
version: "1.x"
framework: Node.js
last_verified: "2025-12-26"
always_attach: false
priority: 6
triggers:
  - drizzle
  - drizzle-orm
  - drizzle-kit
  - pgTable
  - jsonb
  - $type
  - db:push
  - db:generate
  - db:migrate
  - migration
  - postgres
  - postgresql
---

<!--
LLM INSTRUCTION: Use for PostgreSQL + Drizzle ORM. Avoid Prisma/TypeORM patterns.
Schema lives in TypeScript with pgTable. Indexes defined in the pgTable callback.
Use jsonb.$type<T>() for compile-time typing only (no runtime validation).
Use pg Pool with a single shared connection pool.
Migrations: db:push for dev; db:generate + db:migrate for prod.
Advanced indexes (GIN/where/using) may require custom SQL migrations.
-->

# Drizzle ORM (PostgreSQL)

> **Target:** Drizzle ORM + PostgreSQL | **Last Verified:** 2025-12-26

## 1. What AI Models Get Wrong

- **Mixing ORMs** (Prisma schema, TypeORM decorators).
- **Missing pgTable callback** for indexes/constraints.
- **Assuming $type validates at runtime** (it does not).
- **Creating a Pool per request** instead of a shared Pool.
- **Using db:push in prod** instead of migrations.

## 2. Golden Rules

### ✅ DO
- **Define schema in TS** with `pgTable` and column builders.
- **Use jsonb.$type<T>()** to lock TypeScript types (compile-time only).
- **Define indexes** in the `pgTable(..., (t) => [ ... ])` callback.
- **Use a shared `pg.Pool`** and pass it to `drizzle({ client: pool })`.
- **Dev:** `db:push`. **Prod:** `db:generate` + `db:migrate`.

### ❌ DON'T
- **Don't add Prisma/TypeORM files** (`schema.prisma`, `@Entity()`).
- **Don't expect $type to validate data** at runtime.
- **Don't rely on advanced index features** without verifying drizzle-kit output.

## 3. Minimal Setup (Files)

```
src/db/client.ts
src/db/schema.ts
drizzle.config.ts
```

## 4. Core Patterns

### Postgres client (`src/db/client.ts`)
```ts
import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from './schema';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 2_000
});

export const db = drizzle({ client: pool, schema });
```

### Schema + JSONB typing (`src/db/schema.ts`)
```ts
import { pgTable, text, jsonb, uuid, index } from 'drizzle-orm/pg-core';

type UserSettings = {
  theme: 'light' | 'dark';
  marketingOptIn: boolean;
};

export const users = pgTable(
  'users',
  {
    id: uuid('id').defaultRandom().primaryKey(),
    email: text('email').notNull(),
    settings: jsonb('settings').$type<UserSettings>().notNull()
  },
  (t) => [index('users_email_idx').on(t.email)]
);
```

### JSONB query with sql
```ts
import { sql, eq } from 'drizzle-orm';
import { users } from './schema';

await db
  .select()
  .from(users)
  .where(eq(sql`${users.settings} ->> 'theme'`, 'dark'));
```

### Migration scripts
```json
{
  "scripts": {
    "db:push": "drizzle-kit push",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate"
  }
}
```

## 5. Checklist

- [ ] Schema uses `pgTable` + TS columns.
- [ ] JSONB uses `.$type<T>()` for compile-time typing.
- [ ] Indexes defined in the `pgTable` callback.
- [ ] Shared `pg.Pool` passed to `drizzle`.
- [ ] Dev uses `db:push`; prod uses `db:generate` + `db:migrate`.

import { z } from 'zod';
import { insertItemSchema, insertProjectSchema, items, projects } from './schema';

// === SHARED ERROR SCHEMAS ===
export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
  internal: z.object({
    message: z.string(),
  }),
};

// === API CONTRACT ===
export const api = {
  items: {
    list: {
      method: 'GET' as const,
      path: '/api/items',
      responses: {
        200: z.array(z.custom<typeof items.$inferSelect>()),
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/items/:id',
      responses: {
        200: z.custom<typeof items.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/items',
      input: insertItemSchema,
      responses: {
        201: z.custom<typeof items.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
    update: {
      method: 'PUT' as const,
      path: '/api/items/:id',
      input: insertItemSchema.partial(),
      responses: {
        200: z.custom<typeof items.$inferSelect>(),
        400: errorSchemas.validation,
        404: errorSchemas.notFound,
      },
    },
    delete: {
      method: 'DELETE' as const,
      path: '/api/items/:id',
      responses: {
        204: z.void(),
        404: errorSchemas.notFound,
      },
    },
  },
  projects: {
    list: {
      method: 'GET' as const,
      path: '/api/projects',
      responses: {
        200: z.array(z.custom<typeof projects.$inferSelect>()),
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/projects',
      input: insertProjectSchema,
      responses: {
        201: z.custom<typeof projects.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
    update: {
      method: 'PUT' as const,
      path: '/api/projects/:id',
      input: insertProjectSchema.partial(),
      responses: {
        200: z.custom<typeof projects.$inferSelect>(),
        400: errorSchemas.validation,
        404: errorSchemas.notFound,
      },
    },
    delete: {
      method: 'DELETE' as const,
      path: '/api/projects/:id',
      responses: {
        204: z.void(),
        404: errorSchemas.notFound,
      },
    },
  },
  system: {
    export: {
      method: 'GET' as const,
      path: '/api/system/export',
      responses: {
        200: z.object({
          projects: z.array(z.custom<typeof projects.$inferSelect>()),
          items: z.array(z.custom<typeof items.$inferSelect>()),
          exportedAt: z.string(),
        }),
      },
    },
    import: {
      method: 'POST' as const,
      path: '/api/system/import',
      input: z.object({
        projects: z.array(z.any()),
        items: z.array(z.any()),
      }),
      responses: {
        200: z.object({ success: z.boolean(), message: z.string() }),
      },
    }
  }
};

// === BUILD URL HELPER ===
export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}

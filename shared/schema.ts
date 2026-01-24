import { pgTable, text, serial, integer, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { relations } from "drizzle-orm";

// === TABLE DEFINITIONS ===

export const projects = pgTable("projects", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  outcome: text("outcome"),
  status: text("status").notNull().default("active"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const items = pgTable("items", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  notes: text("notes"),
  status: text("status").notNull().default("inbox"), // inbox, someday, projects
  projectId: integer("project_id").references(() => projects.id),
  startTime: text("start_time"), // e.g. "09:00"
  dueDatetime: timestamp("due_datetime"), // Date part used for calendar
  position: integer("position").default(0), // For ordering within projects
  createdAt: timestamp("created_at").defaultNow(),
});

// === RELATIONS ===

export const projectsRelations = relations(projects, ({ many }) => ({
  items: many(items),
}));

export const itemsRelations = relations(items, ({ one }) => ({
  project: one(projects, {
    fields: [items.projectId],
    references: [projects.id],
  }),
}));

// === BASE SCHEMAS ===

export const insertProjectSchema = createInsertSchema(projects).omit({ id: true, createdAt: true });
export const insertItemSchema = createInsertSchema(items).omit({ id: true, createdAt: true });

// === API TYPES ===

export type Project = typeof projects.$inferSelect;
export type InsertProject = z.infer<typeof insertProjectSchema>;

export type Item = typeof items.$inferSelect;
export type InsertItem = z.infer<typeof insertItemSchema>;

export type CreateProjectRequest = InsertProject;
export type UpdateProjectRequest = Partial<InsertProject>;

export type CreateItemRequest = InsertItem;
export type UpdateItemRequest = Partial<InsertItem>;

export type GtdDataExport = {
  projects: Project[];
  items: Item[];
  exportedAt: string;
};

import { pgTable, text, serial, integer, timestamp, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { relations } from "drizzle-orm";

// === TABLE DEFINITIONS ===

export const projects = pgTable("projects", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  outcome: text("outcome"), // "What does 'done' look like?"
  status: text("status").notNull().default("active"), // active, completed, archived
  createdAt: timestamp("created_at").defaultNow(),
});

export const items = pgTable("items", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  notes: text("notes"),
  status: text("status").notNull().default("inbox"), // inbox, next, waiting, someday, reference, done, trash
  projectId: integer("project_id").references(() => projects.id),
  timeEstimate: text("time_estimate"), // e.g. "5m", "1h"
  energyLevel: text("energy_level"), // low, medium, high
  dueDatetime: timestamp("due_datetime"), // For calendar items ONLY
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

// Requests
export type CreateProjectRequest = InsertProject;
export type UpdateProjectRequest = Partial<InsertProject>;

export type CreateItemRequest = InsertItem;
export type UpdateItemRequest = Partial<InsertItem>;

// Import/Export
export type GtdDataExport = {
  projects: Project[];
  items: Item[];
  exportedAt: string;
};

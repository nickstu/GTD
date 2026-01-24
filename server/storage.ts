import { db } from "./db";
import {
  items, projects,
  type Item, type InsertItem, type UpdateItemRequest,
  type Project, type InsertProject, type UpdateProjectRequest,
  type GtdDataExport
} from "@shared/schema";
import { eq, sql } from "drizzle-orm";

export interface IStorage {
  // Items
  getItems(): Promise<Item[]>;
  getItem(id: number): Promise<Item | undefined>;
  createItem(item: InsertItem): Promise<Item>;
  updateItem(id: number, updates: UpdateItemRequest): Promise<Item>;
  deleteItem(id: number): Promise<void>;

  // Projects
  getProjects(): Promise<Project[]>;
  getProject(id: number): Promise<Project | undefined>;
  createProject(project: InsertProject): Promise<Project>;
  updateProject(id: number, updates: UpdateProjectRequest): Promise<Project>;
  deleteProject(id: number): Promise<void>;

  // System
  exportData(): Promise<GtdDataExport>;
  importData(data: GtdDataExport): Promise<void>;
}

export class DatabaseStorage implements IStorage {
  // Items
  async getItems(): Promise<Item[]> {
    return await db.select().from(items).orderBy(items.createdAt);
  }

  async getItem(id: number): Promise<Item | undefined> {
    const [item] = await db.select().from(items).where(eq(items.id, id));
    return item;
  }

  async createItem(insertItem: InsertItem): Promise<Item> {
    const [item] = await db.insert(items).values(insertItem).returning();
    return item;
  }

  async updateItem(id: number, updates: UpdateItemRequest): Promise<Item> {
    const [updated] = await db.update(items)
      .set(updates)
      .where(eq(items.id, id))
      .returning();
    return updated;
  }

  async deleteItem(id: number): Promise<void> {
    await db.delete(items).where(eq(items.id, id));
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    return await db.select().from(projects).orderBy(projects.createdAt);
  }

  async getProject(id: number): Promise<Project | undefined> {
    const [project] = await db.select().from(projects).where(eq(projects.id, id));
    return project;
  }

  async createProject(insertProject: InsertProject): Promise<Project> {
    const [project] = await db.insert(projects).values(insertProject).returning();
    return project;
  }

  async updateProject(id: number, updates: UpdateProjectRequest): Promise<Project> {
    const [updated] = await db.update(projects)
      .set(updates)
      .where(eq(projects.id, id))
      .returning();
    return updated;
  }

  async deleteProject(id: number): Promise<void> {
    await db.delete(projects).where(eq(projects.id, id));
  }

  // System
  async exportData(): Promise<GtdDataExport> {
    const allProjects = await this.getProjects();
    const allItems = await this.getItems();
    return {
      projects: allProjects,
      items: allItems,
      exportedAt: new Date().toISOString()
    };
  }

  async importData(data: GtdDataExport): Promise<void> {
    // Transactional clear and replace would be ideal, but for now we'll just append/upsert logic
    // Actually for a clean import, let's truncate. Warning: Destructive!
    // Since this is a simple app, we will assume "Import" replaces everything or adds to it.
    // Let's implement as "Append" for safety, or we could delete all.
    // Given the request "Persist locally / export / import", usually implies restoring state.
    // Let's keep it safe: clear existing and re-insert.

    await db.transaction(async (tx) => {
      // Delete all existing data
      await tx.delete(items);
      await tx.delete(projects);

      // Insert new data (preserving IDs if possible, or mapping them?)
      // PostgreSQL serials might get messy if we force IDs.
      // Better to drop IDs and re-insert, but that breaks internal relationships.
      // We should insert with explicit IDs if we want to preserve relationships.

      if (data.projects.length > 0) {
        await tx.insert(projects).values(data.projects.map(p => ({
            ...p,
            createdAt: p.createdAt ? new Date(p.createdAt) : new Date()
        })));
        // Reset sequence for projects
        const maxProjectId = Math.max(...data.projects.map(p => p.id), 0);
        await tx.execute(sql.raw(`SELECT setval('projects_id_seq', ${maxProjectId}, true)`));
      }

      if (data.items.length > 0) {
        await tx.insert(items).values(data.items.map(i => ({
            ...i,
            createdAt: i.createdAt ? new Date(i.createdAt) : new Date(),
            dueDatetime: i.dueDatetime ? new Date(i.dueDatetime) : null
        })));
        // Reset sequence for items
        const maxItemId = Math.max(...data.items.map(i => i.id), 0);
        await tx.execute(sql.raw(`SELECT setval('items_id_seq', ${maxItemId}, true)`));
      }
    });
  }
}

export const storage = new DatabaseStorage();

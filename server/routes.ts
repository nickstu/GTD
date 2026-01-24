import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {

  // Items
  app.get(api.items.list.path, async (req, res) => {
    const items = await storage.getItems();
    res.json(items);
  });

  app.get(api.items.get.path, async (req, res) => {
    const item = await storage.getItem(Number(req.params.id));
    if (!item) return res.status(404).json({ message: "Item not found" });
    res.json(item);
  });

  app.post(api.items.create.path, async (req, res) => {
    try {
      const input = api.items.create.input.parse(req.body);
      const item = await storage.createItem(input);
      res.status(201).json(item);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message });
      }
      throw err;
    }
  });

  app.put(api.items.update.path, async (req, res) => {
    try {
      const input = api.items.update.input.parse(req.body);
      const item = await storage.updateItem(Number(req.params.id), input);
      res.json(item);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message });
      }
      res.status(404).json({ message: "Item not found" });
    }
  });

  app.delete(api.items.delete.path, async (req, res) => {
    await storage.deleteItem(Number(req.params.id));
    res.status(204).send();
  });

  // Projects
  app.get(api.projects.list.path, async (req, res) => {
    const projects = await storage.getProjects();
    res.json(projects);
  });

  app.post(api.projects.create.path, async (req, res) => {
    try {
      const input = api.projects.create.input.parse(req.body);
      const project = await storage.createProject(input);
      res.status(201).json(project);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message });
      }
      throw err;
    }
  });

  app.put(api.projects.update.path, async (req, res) => {
    try {
      const input = api.projects.update.input.parse(req.body);
      const project = await storage.updateProject(Number(req.params.id), input);
      res.json(project);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message });
      }
      res.status(404).json({ message: "Project not found" });
    }
  });

  app.delete(api.projects.delete.path, async (req, res) => {
    await storage.deleteProject(Number(req.params.id));
    res.status(204).send();
  });

  // System
  app.get(api.system.export.path, async (req, res) => {
    const data = await storage.exportData();
    res.json(data);
  });

  app.post(api.system.import.path, async (req, res) => {
    try {
      // Basic validation
      const data = req.body;
      if (!Array.isArray(data.items) || !Array.isArray(data.projects)) {
        return res.status(400).json({ message: "Invalid format" });
      }
      await storage.importData(data);
      res.json({ success: true, message: "Import successful" });
    } catch (err) {
      res.status(500).json({ message: "Import failed" });
    }
  });

  await seedDatabase();

  return httpServer;
}

// Seed data function to populate initial state
export async function seedDatabase() {
  const existingItems = await storage.getItems();
  if (existingItems.length === 0) {
    // Create a sample project
    const project = await storage.createProject({
      name: "Learn GTD",
      outcome: "Master the art of stress-free productivity",
      status: "active"
    });

    // Create some sample items
    await storage.createItem({
      title: "Process this inbox item",
      notes: "Decide if this is actionable. If yes, what's the next action?",
      status: "inbox",
      contexts: ["@computer"]
    });

    await storage.createItem({
      title: "Read 'Getting Things Done'",
      status: "next",
      projectId: project.id,
      contexts: ["@reading", "@home"],
      energyLevel: "medium",
      timeEstimate: "2h"
    });

    await storage.createItem({
      title: "Weekly Review",
      status: "next",
      contexts: ["@review"],
      notes: "Empty head, process inbox, review lists.",
      energyLevel: "high"
    });
    
    await storage.createItem({
      title: "Buy replacement batteries",
      status: "errands",
      contexts: ["@errands", "@store"],
      energyLevel: "low"
    });
  }
}

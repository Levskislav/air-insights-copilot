/**
 * OutdoorMate Teams Bot - Entry Point
 * 
 * This is the main entry point for the Teams Message Extension bot.
 * It sets up Express server, Bot Framework adapter, and handles incoming requests.
 */

import express, { Request, Response } from "express";
import {
  CloudAdapter,
  ConfigurationServiceClientCredentialFactory,
  ConfigurationBotFrameworkAuthentication,
  TurnContext,
} from "botbuilder";

import { SearchApp } from "./searchApp";
import config, { validateConfig } from "./config";

// =============================================================================
// Configuration Validation
// =============================================================================

try {
  validateConfig();
} catch (error) {
  console.error("Configuration error:", error);
  // In development, continue with warnings; in production, exit
  if (process.env.NODE_ENV === "production") {
    process.exit(1);
  }
}

// =============================================================================
// Bot Framework Setup
// =============================================================================

const credentialsFactory = new ConfigurationServiceClientCredentialFactory(config);

const botFrameworkAuthentication = new ConfigurationBotFrameworkAuthentication(
  {},
  credentialsFactory
);

const adapter = new CloudAdapter(botFrameworkAuthentication);

// =============================================================================
// Error Handling
// =============================================================================

/**
 * Global error handler for bot turn errors
 * Logs errors and sends user-friendly message
 */
const onTurnErrorHandler = async (context: TurnContext, error: Error): Promise<void> => {
  // Log error details (in production, use proper logging service like Application Insights)
  console.error(`[onTurnError] Unhandled error:`, {
    message: error.message,
    stack: process.env.NODE_ENV === "development" ? error.stack : undefined,
    timestamp: new Date().toISOString(),
  });

  // Send trace activity for Bot Framework Emulator
  await context.sendTraceActivity(
    "OnTurnError Trace",
    error.message,
    "https://www.botframework.com/schemas/error",
    "TurnError"
  );

  // Send user-friendly error message (don't expose internal details)
  await context.sendActivity(
    "Sorry, something went wrong. Please try again later."
  );
};

adapter.onTurnError = onTurnErrorHandler;

// =============================================================================
// Bot Instance
// =============================================================================

const searchApp = new SearchApp();

// =============================================================================
// Express Server Setup
// =============================================================================

const app = express();
app.use(express.json());

const PORT = process.env.PORT || process.env.port || 3978;

// -----------------------------------------------------------------------------
// Health Check Endpoint
// -----------------------------------------------------------------------------

/**
 * Health check endpoint for monitoring and load balancers
 */
app.get("/health", (_req: Request, res: Response) => {
  res.status(200).json({
    status: "healthy",
    timestamp: new Date().toISOString(),
    service: "outdoormate-teams-bot",
    version: process.env.npm_package_version || "1.0.0",
  });
});

/**
 * Readiness check - verifies the bot is ready to receive requests
 */
app.get("/ready", (_req: Request, res: Response) => {
  // Add additional checks here if needed (e.g., database connectivity)
  res.status(200).json({
    ready: true,
    timestamp: new Date().toISOString(),
  });
});

// -----------------------------------------------------------------------------
// Bot Messaging Endpoint
// -----------------------------------------------------------------------------

/**
 * Main endpoint for Bot Framework messages
 * All Teams interactions come through this endpoint
 */
app.post("/api/messages", async (req: Request, res: Response) => {
  await adapter.process(req, res, async (context) => {
    await searchApp.run(context);
  });
});

// -----------------------------------------------------------------------------
// 404 Handler
// -----------------------------------------------------------------------------

app.use((_req: Request, res: Response) => {
  res.status(404).json({
    error: "Not Found",
    message: "The requested endpoint does not exist",
  });
});

// =============================================================================
// Server Startup
// =============================================================================

const server = app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║                    OutdoorMate Teams Bot                       ║
╠════════════════════════════════════════════════════════════════╣
║  Status:    🟢 Running                                         ║
║  Port:      ${String(PORT).padEnd(47)}║
║  Health:    http://localhost:${PORT}/health                      ║
║  Endpoint:  http://localhost:${PORT}/api/messages                ║
╚════════════════════════════════════════════════════════════════╝
  `);
});

// =============================================================================
// Graceful Shutdown
// =============================================================================

/**
 * Handles graceful shutdown on SIGTERM/SIGINT
 * Ensures all connections are properly closed before exit
 */
function gracefulShutdown(signal: string): void {
  console.log(`\n${signal} received. Shutting down gracefully...`);
  
  server.close((err) => {
    if (err) {
      console.error("Error during shutdown:", err);
      process.exit(1);
    }
    console.log("Server closed. Goodbye! 👋");
    process.exit(0);
  });

  // Force close after 10 seconds
  setTimeout(() => {
    console.error("Forced shutdown after timeout");
    process.exit(1);
  }, 10000);
}

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));

// Handle uncaught exceptions
process.on("uncaughtException", (error) => {
  console.error("Uncaught Exception:", error);
  gracefulShutdown("uncaughtException");
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
});

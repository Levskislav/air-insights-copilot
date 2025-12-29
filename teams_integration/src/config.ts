/**
 * Bot Framework configuration
 * Loaded from environment variables
 */

export interface BotConfig {
  MicrosoftAppId: string | undefined;
  MicrosoftAppType: string | undefined;
  MicrosoftAppTenantId: string | undefined;
  MicrosoftAppPassword: string | undefined;
}

const config: BotConfig = {
  MicrosoftAppId: process.env.BOT_ID,
  MicrosoftAppType: process.env.BOT_TYPE || "MultiTenant",
  MicrosoftAppTenantId: process.env.BOT_TENANT_ID,
  MicrosoftAppPassword: process.env.BOT_PASSWORD,
};

/**
 * Validates that required configuration is present
 * @throws Error if required config is missing (only in production)
 */
export function validateConfig(): void {
  const isProduction = process.env.NODE_ENV === "production";
  
  if (isProduction) {
    if (!config.MicrosoftAppId) {
      throw new Error("Missing required environment variable: BOT_ID");
    }
    if (!config.MicrosoftAppPassword) {
      throw new Error("Missing required environment variable: BOT_PASSWORD");
    }
  }
}

export default config;

import axios, { AxiosError } from "axios";
import {
  TeamsActivityHandler,
  CardFactory,
  TurnContext,
  MessagingExtensionQuery,
  MessagingExtensionResponse,
} from "botbuilder";
import * as ACData from "adaptivecards-templating";
import weatherCard from "./adaptiveCards/weatherCard.json";

// =============================================================================
// Configuration
// =============================================================================

const CONFIG = {
  /** OutdoorMate API base URL - defaults to localhost for Codespaces deployment */
  apiUrl: process.env.OUTDOORMATE_API_URL || "http://localhost:8000",
  /** Request timeout in milliseconds */
  requestTimeout: 10000,
  /** Minimum search query length */
  minQueryLength: 2,
} as const;

/** Air quality thresholds based on EPA standards */
const AIR_QUALITY_THRESHOLDS = {
  GOOD: 12,      // PM2.5 ≤ 12 μg/m³
  MODERATE: 35,  // PM2.5 ≤ 35 μg/m³
  // Above 35 is considered unhealthy
} as const;

// =============================================================================
// Types
// =============================================================================

interface WeatherResponse {
  pm25_avg: number;
  pm10_avg: number;
  temp_avg: number;
  snowfall_sum: number;
  snow_depth_avg: number;
  guidance_text: string;
}

interface WeatherCardData {
  location: string;
  temperature: string;
  pm25: string;
  pm10: string;
  airQualityStatus: string;
  snowDepth: string;
  snowfall: string;
  guidance: string;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Determines air quality status based on PM2.5 levels
 * @param pm25 - PM2.5 concentration in μg/m³
 * @returns Human-readable air quality status with emoji
 */
function getAirQualityStatus(pm25: number | null | undefined): string {
  if (pm25 == null) return "Unknown ⚪";
  if (pm25 <= AIR_QUALITY_THRESHOLDS.GOOD) return "Good 🟢";
  if (pm25 <= AIR_QUALITY_THRESHOLDS.MODERATE) return "Moderate 🟡";
  return "Unhealthy 🔴";
}

/**
 * Safely formats a number to fixed decimal places
 * @param value - Number to format
 * @param decimals - Number of decimal places (default: 1)
 * @param fallback - Fallback value if number is invalid
 */
function formatNumber(
  value: number | null | undefined,
  decimals: number = 1,
  fallback: string = "N/A"
): string {
  if (value == null || isNaN(value)) return fallback;
  return value.toFixed(decimals);
}

/**
 * Sanitizes user input to prevent injection attacks
 * @param input - Raw user input
 * @returns Sanitized string
 */
function sanitizeInput(input: string): string {
  return input
    .trim()
    .substring(0, 100) // Limit length
    .replace(/[<>\"'&]/g, ""); // Remove potentially dangerous characters
}

/**
 * Creates an empty result response
 */
function createEmptyResponse(): MessagingExtensionResponse {
  return {
    composeExtension: {
      type: "result",
      attachmentLayout: "list",
      attachments: [],
    },
  };
}

/**
 * Creates an error response card
 * @param location - The location that was searched
 * @param errorMessage - Optional specific error message
 */
function createErrorResponse(
  location: string,
  errorMessage?: string
): MessagingExtensionResponse {
  const message = errorMessage || `Could not get weather for "${location}". Please try again.`;
  const errorCard = CardFactory.heroCard("❌ Weather Unavailable", message);

  return {
    composeExtension: {
      type: "result",
      attachmentLayout: "list",
      attachments: [{ ...errorCard, preview: errorCard }],
    },
  };
}

// =============================================================================
// Main Search App Class
// =============================================================================

/**
 * Teams Message Extension for OutdoorMate weather queries
 * Handles search queries and returns weather data as Adaptive Cards
 */
export class SearchApp extends TeamsActivityHandler {
  /**
   * Handles Teams Messaging Extension search queries
   * @param context - Turn context from Bot Framework
   * @param query - The search query from Teams
   * @returns MessagingExtensionResponse with weather data or error
   */
  public async handleTeamsMessagingExtensionQuery(
    context: TurnContext,
    query: MessagingExtensionQuery
  ): Promise<MessagingExtensionResponse> {
    // Validate query parameters exist
    const rawQuery = query.parameters?.[0]?.value;
    if (!rawQuery || typeof rawQuery !== "string") {
      return createEmptyResponse();
    }

    // Sanitize and validate input
    const searchQuery = sanitizeInput(rawQuery);
    if (searchQuery.length < CONFIG.minQueryLength) {
      return createEmptyResponse();
    }

    try {
      const weatherData = await this.fetchWeatherData(searchQuery);
      return this.createWeatherResponse(searchQuery, weatherData);
    } catch (error) {
      return this.handleError(error, searchQuery);
    }
  }

  /**
   * Fetches weather data from OutdoorMate API
   * @param location - Location to get weather for
   * @returns Weather data from API
   */
  private async fetchWeatherData(location: string): Promise<WeatherResponse> {
    const response = await axios.post<WeatherResponse>(
      `${CONFIG.apiUrl}/analyze`,
      {
        place_name: location,
        hours: 1,
      },
      {
        headers: { "Content-Type": "application/json" },
        timeout: CONFIG.requestTimeout,
      }
    );

    return response.data;
  }

  /**
   * Creates a MessagingExtensionResponse with weather data
   * @param location - The searched location
   * @param weatherData - Weather data from API
   */
  private createWeatherResponse(
    location: string,
    weatherData: WeatherResponse
  ): MessagingExtensionResponse {
    const cardData: WeatherCardData = {
      location,
      temperature: formatNumber(weatherData.temp_avg),
      pm25: formatNumber(weatherData.pm25_avg),
      pm10: formatNumber(weatherData.pm10_avg),
      airQualityStatus: getAirQualityStatus(weatherData.pm25_avg),
      snowDepth: formatNumber(weatherData.snow_depth_avg, 1, "0"),
      snowfall: formatNumber(weatherData.snowfall_sum, 1, "0"),
      guidance: weatherData.guidance_text || "No guidance available",
    };

    const template = new ACData.Template(weatherCard);
    const card = template.expand({ $root: cardData });

    const preview = CardFactory.heroCard(
      `🌡️ ${location}: ${cardData.temperature}°C`,
      `PM2.5: ${cardData.pm25} | Snow: ${cardData.snowDepth}cm`
    );

    const attachment = { ...CardFactory.adaptiveCard(card), preview };

    return {
      composeExtension: {
        type: "result",
        attachmentLayout: "list",
        attachments: [attachment],
      },
    };
  }

  /**
   * Handles errors from weather API calls
   * @param error - The caught error
   * @param location - The location that was searched
   */
  private handleError(error: unknown, location: string): MessagingExtensionResponse {
    // Log error for debugging (in production, use proper logging service)
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      console.error(`OutdoorMate API error for "${location}":`, {
        status: axiosError.response?.status,
        message: axiosError.message,
        url: axiosError.config?.url,
      });

      // Provide user-friendly error messages based on error type
      if (axiosError.code === "ECONNABORTED") {
        return createErrorResponse(location, "Request timed out. Please try again.");
      }
      if (axiosError.response?.status === 404) {
        return createErrorResponse(location, `Location "${location}" not found.`);
      }
      if (axiosError.response?.status === 429) {
        return createErrorResponse(location, "Too many requests. Please wait and try again.");
      }
    } else {
      console.error(`Unexpected error for "${location}":`, error);
    }

    return createErrorResponse(location);
  }
}

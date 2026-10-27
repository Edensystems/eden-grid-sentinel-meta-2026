/**
 * Firebase Functions v2 – EDEN Agent Orchestrator
 * Sense → Think → Learn → Act
 */

const { onValueCreated } = require("firebase-functions/v2/database");
const { setGlobalOptions } = require("firebase-functions/v2");
const { defineString } = require("firebase-functions/params");
const logger = require("firebase-functions/logger");
const axios = require("axios");

// Global options (cost & safety)
setGlobalOptions({
  region: "us-central1",
  maxInstances: 10,
});

// ===== Environment Parameters (v2 ONLY) =====
const THINK_URL = defineString("THINK_URL");
const LEARN_URL = defineString("LEARN_URL");
const ACT_URL = defineString("ACT_URL");

// ===== SENSE → THINK =====
exports.onSenseDataCreated = onValueCreated(
  "eden/community_001/sense_data/{senseId}",
  async (event) => {
    const senseId = event.params.senseId;

    try {
      logger.info("Sense detected → triggering THINK", { senseId });

      await axios.post(THINK_URL.value(), {
        senseId,
      });

      logger.info("THINK agent triggered successfully", { senseId });
    } catch (error) {
      logger.error("THINK agent failed", {
        senseId,
        error: error.message,
      });
    }
  },
);

// ===== THINK → LEARN =====
exports.onThinkOutputCreated = onValueCreated(
  "eden/community_001/think_output/{thinkId}",
  async (event) => {
    const thinkId = event.params.thinkId;

    try {
      logger.info("Think output detected → triggering LEARN", { thinkId });

      await axios.post(LEARN_URL.value(), {
        thinkId,
      });

      logger.info("LEARN agent triggered successfully", { thinkId });
    } catch (error) {
      logger.error("LEARN agent failed", {
        thinkId,
        error: error.message,
      });
    }
  },
);

// ===== LEARN → ACT =====
exports.onLearnTaskCreated = onValueCreated(
  "eden/community_001/learn/tasks/{taskId}",
  async (event) => {
    const taskId = event.params.taskId;

    try {
      logger.info("Learn task detected → triggering ACT", { taskId });

      await axios.post(ACT_URL.value(), {
        taskId,
      });

      logger.info("ACT agent triggered successfully", { taskId });
    } catch (error) {
      logger.error("ACT agent failed", {
        taskId,
        error: error.message,
      });
    }
  },
);

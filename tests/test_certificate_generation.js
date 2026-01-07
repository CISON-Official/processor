#!/usr/bin/env node
import amqp from "amqplib";
import { v4 as uuidv4 } from "uuid";
import crypto from "crypto";

const AMQP_URL = "amqp://localhost";
const EXCHANGE = "certification";
const ROUTING_KEY = "certification";
const TASK_NAME = "certification.first_tasks";

// Shared secret (same on worker)
const SHARED_SECRET = "super-secret-key";

function sign(payload) {
  return crypto
    .createHmac("sha256", SHARED_SECRET)
    .update(payload)
    .digest("hex");
}

async function sendTask() {
  const connection = await amqp.connect(AMQP_URL);
  const channel = await connection.createChannel();

  const taskId = uuidv4();
  const correlationId = uuidv4();

  const args = [
    {
      name: "Fidelugwuowo Dilibe",
      certificate_name: "Working man",
    },
  ];

  const body = Buffer.from(JSON.stringify(args)).toString("base64");
  const signature = sign(body);

  const message = {
    body,
  };

  channel.publish(
    EXCHANGE,
    ROUTING_KEY,
    Buffer.from(JSON.stringify(message)),
    {
      contentType: "application/json",
      deliveryMode: 2, // persistent
      correlationId,
      messageId: taskId,
      timestamp: Date.now(),
    }
  );

  console.log("✅ Task sent");
  console.log("task_id:", taskId);
  console.log("correlation_id:", correlationId);

  await channel.close();
  await connection.close();
}

sendTask().catch(console.error);

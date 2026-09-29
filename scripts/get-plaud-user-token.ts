const BASE_URL = "https://platform-us.plaud.ai/developer/api";

// Credentials from backend/.env
const clientId = "client_01ea2571-1839-4dad-b131-aa627d7ea34b";
const secretKey = "sk_4cL52-hbRq9Kl9pqx_oz3g5x6tQPtBr_nPJ0Ca-ONtM";
const userId = "carecompass-demo-user";

async function main(): Promise<void> {
  const basicAuth = Buffer.from(`${clientId}:${secretKey}`).toString("base64");

  console.log("Step 1: Fetching partner access token...");
  const partnerRes = await fetch(`${BASE_URL}/oauth/partner/access-token`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${basicAuth}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  const partnerData = await partnerRes.json();

  if (!partnerRes.ok) {
    console.error(`Partner token error ${partnerRes.status}:`, JSON.stringify(partnerData, null, 2));
    process.exit(1);
  }

  console.log(`✓ Partner token received (expires in ${partnerData.expires_in}s)`);

  console.log("Step 2: Fetching user access token...");
  const userRes = await fetch(`${BASE_URL}/open/partner/users/access-token`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${partnerData.access_token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id: userId, expires_in: 86400 }),
  });

  const userData = await userRes.json();

  if (!userRes.ok) {
    console.error(`User token error ${userRes.status}:`, JSON.stringify(userData, null, 2));
    process.exit(1);
  }

  console.log(`✓ User token received (expires in ${userData.expires_in}s)`);
  console.log("\n=== USER ACCESS TOKEN ===");
  console.log(userData.access_token);
  console.log("\n=== Copy this to ios-plaud-sdk/ios/PartnerConfig.local.xcconfig ===");
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});

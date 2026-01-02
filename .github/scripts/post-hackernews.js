const { chromium } = require("playwright");

/**
 * Posts to Hacker News using Playwright for browser automation
 */
async function postHackerNews({ context }) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Login to HN - specifically target the login form (not the create account form)
    await page.goto("https://news.ycombinator.com/login");
    await page.waitForLoadState("networkidle");

    // Because there are login and create account forms, we need to target the login form specifically
    const loginForm = page.locator('form[action="login"]:not(:has(input[name="creating"]))');
    await loginForm.locator('input[name="acct"]').fill(process.env.HN_USERNAME);
    await loginForm.locator('input[name="pw"]').fill(process.env.HN_PASSWORD);
    await loginForm.locator('input[type="submit"]').click();

    // Wait for login to complete (look for a logout link)
    await page.waitForSelector('a[href^="logout"]', { timeout: 10000 }); // Use href^= to match links that start with "logout"

    // Navigate to submit page and wait for it to load
    await page.goto("https://news.ycombinator.com/submit");
    await page.waitForLoadState("networkidle");

    // Extract social media post from PR body if present
    const description = context.payload.pull_request.body || "";
    let socialPost = null;
    const socialMediaMatch = description.match(/## Social Media Post\s*\n([\s\S]*?)(?=\n##|\n$|$)/i);
    if (socialMediaMatch) 
      socialPost = socialMediaMatch[1].trim();
    
    // Use social media post if available, otherwise PR title
    const title = (socialPost || context.payload.pull_request.title).substring(0, 80);
    const url = "https://gitauto.ai?utm_source=hackernews&utm_medium=referral"
    await page.fill('input[name="title"]', title);
    await page.fill('input[name="url"]', url);

    // If there's a description, submit as a "text" post with both URL and description
    if (description) await page.fill('textarea[name="text"]', description);

    await page.click('input[type="submit"]');
    await page.waitForLoadState("networkidle");

    // Wait for redirect to either newest page or error
    await Promise.race([
      page.waitForURL("https://news.ycombinator.com/newest"),
      page.waitForSelector(".error", { timeout: 10000 }),
    ]);

    // Check if there was an error
    const error = await page
      .locator(".error")
      .first()
      .textContent()
      .catch(() => null);
    if (error) throw new Error(`HN submission failed: ${error}`);

    // Send to Slack webhook
    await fetch(process.env.SLACK_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        msg: `Posted to Hacker News! https://news.ycombinator.com/newest`,
      }),
    });

    await browser.close();
  } catch (error) {
    await browser.close();
    throw error;
  }
}

module.exports = postHackerNews;

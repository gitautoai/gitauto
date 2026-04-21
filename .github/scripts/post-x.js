const extractSocialPosts = require("./extract-social-posts");
const { TwitterApi } = require("twitter-api-v2");

/**
 * @see https://developer.x.com/en/docs/x-api/tweets/manage-tweets/api-reference/post-tweets
 */
async function postX({ context }) {
  // Company account: https://console.x.com/accounts/1868157094207295489/apps
  const clientCompany = new TwitterApi({
    appKey: process.env.X_OAUTH1_CONSUMER_KEY_GITAUTO,
    appSecret: process.env.X_OAUTH1_CONSUMER_KEY_SECRET_GITAUTO,
    accessToken: process.env.X_OAUTH1_ACCESS_TOKEN_GITAUTO,
    accessSecret: process.env.X_OAUTH1_ACCESS_TOKEN_SECRET_GITAUTO,
  });

  // Wes personal account: https://console.x.com/accounts/1880785843574677504/apps
  const clientWes = new TwitterApi({
    appKey: process.env.X_OAUTH1_CONSUMER_KEY_WES,
    appSecret: process.env.X_OAUTH1_CONSUMER_KEY_SECRET_WES,
    accessToken: process.env.X_OAUTH1_ACCESS_TOKEN_WES,
    accessSecret: process.env.X_OAUTH1_ACCESS_TOKEN_SECRET_WES,
  });

  const description = context.payload.pull_request.body || "";
  const { gitautoX: gitautoPost, wesX: wesPost } = extractSocialPosts(description);

  if (!gitautoPost) console.log("No 'GitAuto on X' section, skipping GitAuto tweet");
  if (!wesPost) console.log("No 'Wes on X' section, skipping Wes tweet");
  if (!gitautoPost && !wesPost) return;

  // Senders have to be in the community
  // https://x.com/hnishio0105/communities
  const communityIds = [
    "1670204079619055616", // AI Agents
    "1493446837214187523", // Build in Public
    "1699807431709041070", // Software Engineering
    "1471580197908586507", // Startup Community
    "1498737511241158657", // Startup founders & friends
  ];

  // GitAuto is on X free tier (280 char hard limit). Wes has X Premium so long-form is allowed.
  // https://github.com/PLhery/node-twitter-api-v2/blob/master/doc/v2.md#create-a-tweet
  const postFree = async (client, text) => {
    try {
      return await client.v2.tweet(text);
    } catch (error) {
      if (text.length > 280) {
        const truncated = text.substring(0, 277) + "...";
        return await client.v2.tweet(truncated);
      }
      throw error;
    }
  };

  const postPremium = async (client, text) => client.v2.tweet(text);

  const companyResult = gitautoPost ? await postFree(clientCompany, gitautoPost) : null;
  const wesResult = wesPost ? await postPremium(clientWes, wesPost) : null;

  // https://docs.x.com/x-api/posts/creation-of-a-post
  // const communityPosts = await Promise.all(
  //   communityIds.map(async (communityId) => {
  //     const response = await fetch("https://api.x.com/2/tweets", {
  //       method: "POST",
  //       headers: {
  //         Authorization: `Bearer ${process.env.TWITTER_BEARER_TOKEN_WES}`,
  //         "Content-Type": "application/json",
  //       },
  //       body: JSON.stringify({ text: post, community_id: communityId }),
  //     });

  //     if (!response.ok) {
  //       console.error(`Failed to post to community ${communityId}:`, await response.json());
  //       return null;
  //     }

  //     return await response.json();
  //   })
  // );

  // Wait for a random amount of time
  const getRandomDelay = () => Math.floor(Math.random() * 10000 + 5000);
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  await sleep(getRandomDelay());

  // Like each other's posts (only when both were posted, requires paid X API access)
  // https://github.com/PLhery/node-twitter-api-v2/blob/master/doc/v2.md#like-a-tweet
  if (companyResult && wesResult) {
    try {
      const userCompany = await clientCompany.v2.me();
      await clientCompany.v2.like(userCompany.data.id, wesResult.data.id);
      const userWes = await clientWes.v2.me();
      await clientWes.v2.like(userWes.data.id, companyResult.data.id);
    } catch (error) {
      console.log("Failed to like posts (free tier):", error.message);
    }
  }

  // Send to Slack
  if (process.env.SLACK_BOT_TOKEN) {
    const links = [
      companyResult ? `https://x.com/gitautoai/status/${companyResult.data.id}` : null,
      wesResult ? `https://x.com/hiroshinishio/status/${wesResult.data.id}` : null,
    ].filter(Boolean).join(" and ");
    await fetch("https://slack.com/api/chat.postMessage", {
      method: "POST",
      headers: { "Authorization": `Bearer ${process.env.SLACK_BOT_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({ channel: "C08PHH352S3", text: `Posted to X! ${links}` }),
    });
  } else {
    console.log("SLACK_BOT_TOKEN not set, skipping Slack notification");
  }

}

module.exports = postX;

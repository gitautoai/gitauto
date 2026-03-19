const extractSocialPosts = require("./extract-social-posts");
const { TwitterApi } = require("twitter-api-v2");

/**
 * @see https://developer.x.com/en/docs/x-api/tweets/manage-tweets/api-reference/post-tweets
 */
async function postTwitter({ context }) {
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
  const { gitauto: gitautoTweet, wes: wesTweet } = extractSocialPosts(description);

  if (!gitautoTweet && !wesTweet) {
    console.log("No Social Media Post section found in PR body, skipping Twitter post");
    return;
  }

  // Senders have to be in the community
  // https://x.com/hnishio0105/communities
  const communityIds = [
    "1670204079619055616", // AI Agents
    "1493446837214187523", // Build in Public
    "1699807431709041070", // Software Engineering
    "1471580197908586507", // Startup Community
    "1498737511241158657", // Startup founders & friends
  ];

  // Post tweets and get their IDs
  // https://github.com/PLhery/node-twitter-api-v2/blob/master/doc/v2.md#create-a-tweet
  const postTweet = async (client, text) => {
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

  const companyTweetResult = gitautoTweet ? await postTweet(clientCompany, gitautoTweet) : null;
  const wesTweetResult = wesTweet ? await postTweet(clientWes, wesTweet) : null;

  if (!companyTweetResult && !wesTweetResult) {
    console.log("Both posts are empty, skipping");
    return;
  }

  // https://docs.x.com/x-api/posts/creation-of-a-post
  // const communityTweets = await Promise.all(
  //   communityIds.map(async (communityId) => {
  //     const response = await fetch("https://api.x.com/2/tweets", {
  //       method: "POST",
  //       headers: {
  //         Authorization: `Bearer ${process.env.TWITTER_BEARER_TOKEN_WES}`,
  //         "Content-Type": "application/json",
  //       },
  //       body: JSON.stringify({ text: tweet, community_id: communityId }),
  //     });

  //     if (!response.ok) {
  //       console.error(`Failed to post to community ${communityId}:`, await response.json());
  //       return null;
  //     }

  //     return await response.json();
  //   })
  // );

  // Wait for a random amount of time
  const getRandomDelay = () => Math.floor(Math.random() * 55000 + 5000);
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  await sleep(getRandomDelay());

  // Like each other's tweets (requires paid X API access)
  // https://github.com/PLhery/node-twitter-api-v2/blob/master/doc/v2.md#like-a-tweet
  if (companyTweetResult && wesTweetResult) {
    try {
      const userCompany = await clientCompany.v2.me();
      await clientCompany.v2.like(userCompany.data.id, wesTweetResult.data.id);
      const userWes = await clientWes.v2.me();
      await clientWes.v2.like(userWes.data.id, companyTweetResult.data.id);
    } catch (error) {
      console.log("Failed to like tweets (free tier):", error.message);
    }
  }

  // Send to Slack
  if (process.env.SLACK_BOT_TOKEN) {
    const links = [
      companyTweetResult ? `https://x.com/gitautoai/status/${companyTweetResult.data.id}` : null,
      wesTweetResult ? `https://x.com/hiroshinishio/status/${wesTweetResult.data.id}` : null,
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

module.exports = postTwitter;

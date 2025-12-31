const { TwitterApi } = require("twitter-api-v2");

/**
 * @see https://developer.x.com/en/docs/x-api/tweets/manage-tweets/api-reference/post-tweets
 */
async function postTwitter({ context }) {
  // Company account
  const clientCompany = new TwitterApi({
    appKey: process.env.TWITTER_API_KEY,
    appSecret: process.env.TWITTER_API_SECRET,
    accessToken: process.env.TWITTER_ACCESS_TOKEN,
    accessSecret: process.env.TWITTER_ACCESS_TOKEN_SECRET,
  });

  // Wes personal account
  const clientWes = new TwitterApi({
    appKey: process.env.TWITTER_API_KEY_WES,
    appSecret: process.env.TWITTER_API_SECRET_WES,
    accessToken: process.env.TWITTER_ACCESS_TOKEN_WES,
    accessSecret: process.env.TWITTER_ACCESS_TOKEN_SECRET_WES,
  });

  const message = "🚀 New release";
  const title = context.payload.pull_request.title;
  const description = context.payload.pull_request.body || "";
  const url = "https://gitauto.ai?utm_source=x&utm_medium=referral"

  // Non-paid account, we can only post 280 characters. Paid account can post 250,000 characters.
  const combinedText = description ? `${title}\n${url}\n\n${description}` : `${title}\n${url}`;
  const tweet = `${message}: ${combinedText}`;

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

  const companyTweet = await postTweet(clientCompany, tweet);
  const wesTweet = await postTweet(clientWes, tweet);

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

  // Like each other's tweets
  // https://github.com/PLhery/node-twitter-api-v2/blob/master/doc/v2.md#like-a-tweet
  const userCompany = await clientCompany.v2.me();
  await clientCompany.v2.like(userCompany.data.id, wesTweet.data.id);
  const userWes = await clientWes.v2.me();
  await clientWes.v2.like(userWes.data.id, companyTweet.data.id);
  // await Promise.all(communityTweets.map((tweet) => clientWes.v2.like(tweet.data.id)));

  // Send to Slack webhook
  await fetch(process.env.SLACK_WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      msg: `Posted to X! https://x.com/gitautoai/status/${companyTweet.data.id} and https://x.com/hiroshinishio/status/${wesTweet.data.id}`,
    }),
  });

}

module.exports = postTwitter;

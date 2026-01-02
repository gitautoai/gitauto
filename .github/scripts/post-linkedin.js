const { RestliClient } = require("linkedin-api-client");

const gitautoUrn = "urn:li:organization:100932100"; // Go to company profile page
const wesUrn = "urn:li:person:Nu-Ocwc81N"; // curl -X GET "https://api.linkedin.com/v2/me" -H "Authorization: Bearer YOUR_ACCESS_TOKEN" and get the "id" field

/**
 * @see https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2024-11&viewFallbackFrom=li-lms-unversioned&tabs=http
 */
async function postLinkedIn({ context }) {
  const restliClient = new RestliClient();
  const accessToken = process.env.LINKEDIN_ACCESS_TOKEN;

  const message = "🚀 New release";
  const description = context.payload.pull_request.body || "";
  const url = "https://gitauto.ai?utm_source=linkedin&utm_medium=referral"

  // Extract social media post from PR body if present
  let socialPost = null;
  const socialMediaMatch = description.match(/## Social Media Post\s*\n([\s\S]*?)(?=\n##|\n$|$)/i);
  if (socialMediaMatch) {
    socialPost = socialMediaMatch[1].trim();
  }

  // Fallback to PR title if no social media section
  let title = socialPost || context.payload.pull_request.title;

  // Handle truncated titles with continuation in body
  if (!socialPost && title.endsWith('…') && description) {
    const firstLine = description.split('\n')[0];
    if (firstLine.startsWith('…')) {
      title = title.slice(0, -1) + firstLine.slice(1);
    }
  }

  // Helper function for random delay between 5-15 seconds
  const getRandomDelay = () => Math.floor(Math.random() * 10000 + 5000);
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // Helper function to create a post
  const createPost = async (authorUrn) => {
    return restliClient.create({
      resourcePath: "/posts",
      entity: {
        author: authorUrn,
        commentary: `${message}: ${title}`,
        visibility: "PUBLIC",
        distribution: {
          feedDistribution: "MAIN_FEED",
          targetEntities: [],
          thirdPartyDistributionChannels: [],
        },

        // https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/article-ads-integrations?view=li-lms-2024-11&tabs=http#workflow
        content: {
          article: {
            source: url,
            title: title,
            description: description || `Check out our latest release!`,
          },
        },
        lifecycleState: "PUBLISHED",
        isReshareDisabledByAuthor: false,
      },
      accessToken,
    });
  };

  // Helper function to like a post
  // https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/reactions-api?view=li-lms-2024-11&tabs=http
  const likePost = async (actorUrn, postUrn) => {
    await restliClient.create({
      resourcePath: "/reactions",
      entity: { root: postUrn, reactionType: "LIKE" },
      queryParams: { actor: actorUrn },
      accessToken,
    });
  };

  // Post from both accounts
  const companyPost = await createPost(gitautoUrn);
  const companyPostUrn = companyPost.headers["x-restli-id"];
  const wesPost = await createPost(wesUrn);
  const wesPostUrn = wesPost.headers["x-restli-id"];

  // Wait and like each other's posts
  await sleep(getRandomDelay());
  await likePost(gitautoUrn, wesPostUrn); // Company likes Wes's post
  await likePost(wesUrn, companyPostUrn); // Wes likes Company's post

  // Send the post links to Slack webhook
  await fetch(process.env.SLACK_WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      msg: `Posted to LinkedIn! https://www.linkedin.com/feed/update/urn:li:activity:${companyPostUrn} and https://www.linkedin.com/feed/update/urn:li:activity:${wesPostUrn}`,
    }),
  });
}

module.exports = postLinkedIn;

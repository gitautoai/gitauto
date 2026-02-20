const extractSocialPosts = require("./extract-social-posts");
const { RestliClient } = require("linkedin-api-client");

const gitautoUrn = "urn:li:organization:100932100"; // Go to company profile page
const wesUrn = "urn:li:person:Nu-Ocwc81N"; // curl -X GET "https://api.linkedin.com/v2/me" -H "Authorization: Bearer YOUR_ACCESS_TOKEN" and get the "id" field

/**
 * @see https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2024-11&viewFallbackFrom=li-lms-unversioned&tabs=http
 */
async function postLinkedIn({ context }) {
  const restliClient = new RestliClient();
  const accessToken = process.env.LINKEDIN_ACCESS_TOKEN;

  const description = context.payload.pull_request.body || "";
  const url = "https://gitauto.ai?utm_source=linkedin&utm_medium=referral"
  const { gitauto: gitautoText, wes: wesText } = extractSocialPosts(description);

  if (!gitautoText && !wesText) {
    console.log("No Social Media Post section found in PR body, skipping LinkedIn post");
    return;
  }

  // Helper function for random delay between 5-15 seconds
  const getRandomDelay = () => Math.floor(Math.random() * 10000 + 5000);
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // Helper function to create a post
  const createPost = async (authorUrn, text) => {
    return restliClient.create({
      resourcePath: "/posts",
      entity: {
        author: authorUrn,
        commentary: text,
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
            title: text,
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
  const companyPost = gitautoText ? await createPost(gitautoUrn, gitautoText) : null;
  const companyPostUrn = companyPost?.headers["x-restli-id"];
  const wesPost = wesText ? await createPost(wesUrn, wesText) : null;
  const wesPostUrn = wesPost?.headers["x-restli-id"];

  if (!companyPostUrn && !wesPostUrn) {
    console.log("Both posts are empty, skipping");
    return;
  }

  // Wait and like each other's posts
  if (companyPostUrn && wesPostUrn) {
    await sleep(getRandomDelay());
    await likePost(gitautoUrn, wesPostUrn); // Company likes Wes's post
    await likePost(wesUrn, companyPostUrn); // Wes likes Company's post
  }

  // Send the post links to Slack webhook
  if (process.env.SLACK_WEBHOOK_URL) {
    const links = [
      companyPostUrn ? `https://www.linkedin.com/feed/update/urn:li:activity:${companyPostUrn}` : null,
      wesPostUrn ? `https://www.linkedin.com/feed/update/urn:li:activity:${wesPostUrn}` : null,
    ].filter(Boolean).join(" and ");
    await fetch(process.env.SLACK_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ msg: `Posted to LinkedIn! ${links}` }),
    });
  } else {
    console.log("SLACK_WEBHOOK_URL not set, skipping Slack notification");
  }
}

module.exports = postLinkedIn;

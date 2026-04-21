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
  const { gitautoLinkedIn: gitautoText, wesLinkedIn: wesText } = extractSocialPosts(description);

  if (!gitautoText) console.log("No 'GitAuto on LinkedIn' section, skipping GitAuto post");
  if (!wesText) console.log("No 'Wes on LinkedIn' section, skipping Wes post");
  if (!gitautoText && !wesText) return;

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

  // Post each account independently based on which sections exist
  const companyPost = gitautoText ? await createPost(gitautoUrn, gitautoText) : null;
  const companyPostUrn = companyPost?.headers["x-restli-id"];
  const wesPost = wesText ? await createPost(wesUrn, wesText) : null;
  const wesPostUrn = wesPost?.headers["x-restli-id"];

  // Wait and like each other's posts only when both were posted
  if (companyPostUrn && wesPostUrn) {
    await sleep(getRandomDelay());
    await likePost(gitautoUrn, wesPostUrn); // Company likes Wes's post
    await likePost(wesUrn, companyPostUrn); // Wes likes Company's post
  }

  // Send to Slack
  if (process.env.SLACK_BOT_TOKEN) {
    const links = [
      companyPostUrn ? `https://www.linkedin.com/feed/update/urn:li:activity:${companyPostUrn}` : null,
      wesPostUrn ? `https://www.linkedin.com/feed/update/urn:li:activity:${wesPostUrn}` : null,
    ].filter(Boolean).join(" and ");
    await fetch("https://slack.com/api/chat.postMessage", {
      method: "POST",
      headers: { "Authorization": `Bearer ${process.env.SLACK_BOT_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({ channel: "C08PHH352S3", text: `Posted to LinkedIn! ${links}` }),
    });
  } else {
    console.log("SLACK_BOT_TOKEN not set, skipping Slack notification");
  }
}

module.exports = postLinkedIn;

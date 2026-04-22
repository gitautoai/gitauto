/**
 * Extracts social media posts from PR body.
 * Matrix of author × platform: GitAuto/Wes × X/LinkedIn, plus an optional HN title + body.
 *
 * @param {string} body - PR body text
 * @returns {{ gitautoX: string, gitautoLinkedIn: string, wesX: string, wesLinkedIn: string, hnTitle: string, hnBody: string }}
 */
function extractSocialPosts(body) {
  const section = (label) => {
    const pattern = new RegExp(`## Social Media Post \\(${label}\\)\\s*\\n([\\s\\S]*?)(?=\\n## |\\n$|$)`, "i");
    return body.match(pattern)?.[1]?.trim() || "";
  };

  return {
    gitautoX: section("GitAuto on X"),
    gitautoLinkedIn: section("GitAuto on LinkedIn"),
    wesX: section("Wes on X"),
    wesLinkedIn: section("Wes on LinkedIn"),
    hnTitle: section("HN Title"),
    hnBody: section("HN Body"),
  };
}

module.exports = extractSocialPosts;

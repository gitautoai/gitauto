/**
 * Extracts social media posts from PR body.
 * Supports both new format (separate GitAuto/Wes sections) and legacy single section.
 *
 * @param {string} body - PR body text
 * @returns {{ gitauto: string, wes: string }} Extracted posts (empty string if not found)
 */
function extractSocialPosts(body) {
  const gitautoMatch = body.match(/## Social Media Post \(GitAuto\)\s*\n([\s\S]*?)(?=\n## |\n$|$)/i);
  const wesMatch = body.match(/## Social Media Post \(Wes\)\s*\n([\s\S]*?)(?=\n## |\n$|$)/i);

  // Fall back to single "## Social Media Post" for backward compatibility
  const fallbackMatch = body.match(/## Social Media Post\s*\n([\s\S]*?)(?=\n##|\n$|$)/i);

  return {
    gitauto: (gitautoMatch?.[1] || fallbackMatch?.[1] || "").trim(),
    wes: (wesMatch?.[1] || fallbackMatch?.[1] || "").trim(),
  };
}

module.exports = extractSocialPosts;

const formatDuration = (milliseconds) => {
  if (milliseconds == null) return "—";
  const seconds = Math.round(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return minutes ? `${minutes}m ${rest}s` : `${rest}s`;
};

const escapeHTML = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const timingCard = (group) => {
  const ssh = group.metrics.request_to_ssh_ready;
  const stack = group.metrics.request_to_stack_ready;
  const build = group.metrics.ssh_ready_to_stack_ready;
  const winners = Object.entries(group.long_poles.winner_counts)
    .sort((a, b) => b[1] - a[1]);
  const longPole = winners.length ? winners[0][0].replaceAll("_", " ") : "Not instrumented";
  return `<article class="card">
    <div class="card-top">
      <div><p class="eyebrow">${escapeHTML(group.provider)} · ${escapeHTML(group.cache_state)}</p><h3>${escapeHTML(group.data_center)}</h3></div>
      <span class="badge">${Math.round(group.success_rate * 100)}% ready</span>
    </div>
    <p>${escapeHTML(group.gpu_count)}× ${escapeHTML(group.gpu_sku)}<br>${escapeHTML(group.recipe_id)}</p>
    <dl class="facts">
      <dt>SSH median / p90</dt><dd>${formatDuration(ssh?.median_ms)} / ${formatDuration(ssh?.p90_ms)}</dd>
      <dt>Build median / p90</dt><dd>${formatDuration(build?.median_ms)} / ${formatDuration(build?.p90_ms)}</dd>
      <dt>Total median / p90</dt><dd>${formatDuration(stack?.median_ms)} / ${formatDuration(stack?.p90_ms)}</dd>
      <dt>Observed long pole</dt><dd>${escapeHTML(longPole)}</dd>
      <dt>Samples</dt><dd>${escapeHTML(group.samples)}</dd>
    </dl>
  </article>`;
};

const recipeCard = (recipe) => `<article class="card">
  <div class="card-top">
    <div><p class="eyebrow">${escapeHTML(recipe.runtime.name)} · ${escapeHTML(recipe.model.format)}</p><h3>${escapeHTML(recipe.name)}</h3></div>
    <span class="badge">${escapeHTML(recipe.status)}</span>
  </div>
  <p>${escapeHTML(recipe.model.source)}<br>Bootstrap ${escapeHTML(recipe.bootstrap.sha256.slice(0, 12))}</p>
  <dl class="facts">
    <dt>Minimum VRAM</dt><dd>${escapeHTML(recipe.requirements.minimum_gpu_memory_gb)} GB</dd>
    <dt>GPU count</dt><dd>${escapeHTML(recipe.requirements.gpu_count)}</dd>
    <dt>Workspace</dt><dd>${escapeHTML(recipe.requirements.minimum_workspace_gb)} GB</dd>
    <dt>Verified</dt><dd>${escapeHTML(recipe.verified_day || "Not yet")}</dd>
  </dl>
</article>`;

Promise.all([
  fetch("data/summary.json").then((response) => response.json()),
  fetch("data/recipes.json").then((response) => response.json()),
]).then(([summary, recipes]) => {
  document.querySelector("#dataset-meta").textContent = summary.observation_count
    ? `${summary.observation_count} observations · through ${summary.through_observed_day}`
    : "Ledger initialized · awaiting first contribution";
  document.querySelector("#timing-empty").hidden = summary.groups.length !== 0;
  document.querySelector("#timing-grid").innerHTML = summary.groups.map(timingCard).join("");
  document.querySelector("#recipe-grid").innerHTML = recipes.map(recipeCard).join("");
}).catch((error) => {
  document.querySelector("#dataset-meta").textContent = "Dataset unavailable";
  document.querySelector("#timing-empty").hidden = false;
  console.error(error);
});

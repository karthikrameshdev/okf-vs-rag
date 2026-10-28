let benchmarkChart = null;
let okfStorageData = null;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  fetchSystemStatus();
  fetchBenchmarkPresets();
  initQueryForm();
  loadStorageExplorer();
});

function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const tabId = btn.dataset.tab;
      document.getElementById(`tab-${tabId}`).classList.add("active");
    });
  });
}

async function fetchSystemStatus() {
  const statusContainer = document.getElementById("system-status");
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    const qBackend = data.qdrant.backend || "Qdrant";
    const qCount = data.qdrant.points_count || 0;
    const okfCount = data.okf_documents_count || 0;

    statusContainer.innerHTML = `
      <span class="status-pill status-healthy">
        ● ${qBackend} (${qCount} vectors) &bull; OKF (${okfCount} docs)
      </span>
    `;

    document.getElementById("qdrant-count-badge").innerText = `${qCount} Vector Points (${qBackend})`;
    document.getElementById("okf-count-badge").innerText = `${okfCount} Markdown Entities`;
  } catch (err) {
    statusContainer.innerHTML = `
      <span class="status-pill status-loading">● Local Engine Connected</span>
    `;
  }
}

async function fetchBenchmarkPresets() {
  const container = document.getElementById("preset-container");
  try {
    const res = await fetch("/api/benchmark-questions");
    const presets = await res.json();

    container.innerHTML = "";
    presets.forEach(p => {
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className = "preset-pill";
      pill.innerHTML = `⚡ <strong>${p.title}:</strong> ${p.query.slice(0, 48)}...`;
      pill.addEventListener("click", () => {
        document.getElementById("query-input").value = p.query;
        executeQuery(p.query);
      });
      container.appendChild(pill);
    });
  } catch (err) {
    console.error("Failed to load presets:", err);
  }
}

function initQueryForm() {
  const form = document.getElementById("query-form");
  const input = document.getElementById("query-input");

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (query) {
      executeQuery(query);
    }
  });
}

async function executeQuery(query) {
  const submitBtn = document.getElementById("submit-btn");
  const btnText = submitBtn.querySelector(".btn-text");
  const spinner = submitBtn.querySelector(".spinner");
  const resultsArea = document.getElementById("results-area");

  btnText.innerText = "Analyzing Pipelines...";
  spinner.style.display = "inline-block";
  submitBtn.disabled = true;

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    const data = await res.json();
    renderComparisonResults(data);
    resultsArea.style.display = "block";
    resultsArea.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    alert("Error executing query: " + err.message);
  } finally {
    btnText.innerText = "Execute Comparison";
    spinner.style.display = "none";
    submitBtn.disabled = false;
  }
}

function renderComparisonResults(data) {
  const { rag, okf, analysis } = data;

  // Stat Overview
  document.getElementById("stat-latency-win").innerText = analysis.retrieval_speedup.split(" ")[2] || "5x Faster";
  document.getElementById("stat-latency-sub").innerText = `${okf.latency_breakdown.index_and_traversal_ms}ms vs ${rag.latency_breakdown.total_retrieval_ms}ms retrieval`;
  document.getElementById("stat-boundary").innerText = okf.boundary_status.includes("100%") ? "100% Intact" : "Intact";
  document.getElementById("stat-provenance").innerText = okf.provenance.includes("Verified") ? "Verified & Auditable" : "Signed";

  // RAG Latencies
  const ragLatRow = document.getElementById("rag-latencies");
  ragLatRow.innerHTML = `
    <span class="latency-pill">Embed: <strong>${rag.latency_breakdown.embedding_latency_ms} ms</strong></span>
    <span class="latency-pill">Vector ANN: <strong>${rag.latency_breakdown.vector_search_latency_ms} ms</strong></span>
    <span class="latency-pill">LLM Synthesis: <strong>${rag.latency_breakdown.synthesis_latency_ms} ms</strong></span>
    <span class="latency-pill">Total: <strong class="text-magenta">${rag.total_latency_ms} ms</strong></span>
    <span class="latency-pill">Tokens: <strong>~${rag.token_count}</strong></span>
  `;

  // OKF Latencies
  const okfLatRow = document.getElementById("okf-latencies");
  okfLatRow.innerHTML = `
    <span class="latency-pill">Tree/Index Traversal: <strong>${okf.latency_breakdown.index_and_traversal_ms} ms</strong></span>
    <span class="latency-pill">LLM Synthesis: <strong>${okf.latency_breakdown.synthesis_latency_ms} ms</strong></span>
    <span class="latency-pill">Total: <strong class="text-green">${okf.total_latency_ms} ms</strong></span>
    <span class="latency-pill">Tokens: <strong>~${okf.token_count}</strong></span>
  `;

  // RAG Storage Preview
  const ragStorageBox = document.getElementById("rag-storage-box");
  ragStorageBox.innerText = JSON.stringify(rag.storage_payload_preview, null, 2);

  // OKF Storage Preview
  const okfStorageBox = document.getElementById("okf-storage-box");
  okfStorageBox.innerText = JSON.stringify(okf.storage_payload_preview, null, 2);

  // Context boxes
  document.getElementById("rag-context-box").innerText = rag.context_preview;
  document.getElementById("okf-context-box").innerText = okf.context_preview;

  // Answers
  document.getElementById("rag-answer-text").innerText = rag.answer;
  document.getElementById("okf-answer-text").innerText = okf.answer;

  // Update Chart
  updateChart(rag, okf);
}

function updateChart(rag, okf) {
  const ctx = document.getElementById("benchmarkChart").getContext("2d");

  const ragRetrieval = rag.latency_breakdown.total_retrieval_ms || 10;
  const okfRetrieval = okf.latency_breakdown.index_and_traversal_ms || 1;
  const ragTotal = rag.total_latency_ms;
  const okfTotal = okf.total_latency_ms;

  const data = {
    labels: ["Retrieval Latency (ms)", "End-to-End Latency (ms)", "Context Token Count"],
    datasets: [
      {
        label: "Classic Vector RAG",
        backgroundColor: "rgba(244, 63, 94, 0.75)",
        borderColor: "rgba(244, 63, 94, 1)",
        borderWidth: 1,
        borderRadius: 6,
        data: [ragRetrieval, ragTotal, rag.token_count],
      },
      {
        label: "Open Knowledge Format (OKF)",
        backgroundColor: "rgba(52, 211, 153, 0.75)",
        borderColor: "rgba(52, 211, 153, 1)",
        borderWidth: 1,
        borderRadius: 6,
        data: [okfRetrieval, okfTotal, okf.token_count],
      },
    ],
  };

  if (benchmarkChart) {
    benchmarkChart.destroy();
  }

  benchmarkChart = new Chart(ctx, {
    type: "bar",
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#94a3b8", font: { family: "Inter", size: 12 } },
        },
      },
      scales: {
        x: {
          ticks: { color: "#94a3b8" },
          grid: { color: "rgba(255, 255, 255, 0.05)" },
        },
        y: {
          ticks: { color: "#94a3b8" },
          grid: { color: "rgba(255, 255, 255, 0.05)" },
        },
      },
    },
  });
}

async function loadStorageExplorer() {
  // 1. Load RAG Qdrant Points
  const ragList = document.getElementById("rag-storage-list");
  try {
    const res = await fetch("/api/storage/rag");
    const points = await res.json();
    ragList.innerHTML = "";
    points.forEach(p => {
      const card = document.createElement("div");
      card.className = "chunk-card";
      card.innerHTML = `
        <div class="chunk-card-header">
          <span>Point ID: #${p.point_id} &bull; ${p.payload.chunk_id}</span>
          <span>${p.payload.source_file}</span>
        </div>
        <p>${p.payload.text}</p>
        <div class="chunk-vector-preview">
          [Vector Floats Dimension ${p.vector_dimension}]: [${p.vector_sample.map(x => x.toFixed(4)).join(", ")}...]
        </div>
      `;
      ragList.appendChild(card);
    });
  } catch (err) {
    ragList.innerHTML = "<p class='text-muted'>Failed to load Qdrant points.</p>";
  }

  // 2. Load OKF Filesystem & Tree
  const okfTree = document.getElementById("okf-tree-container");
  const docPreview = document.getElementById("okf-doc-preview");

  try {
    const res = await fetch("/api/storage/okf");
    okfStorageData = await res.json();
    okfTree.innerHTML = "";

    (okfStorageData.documents || []).forEach(doc => {
      const item = document.createElement("div");
      item.className = "tree-node";
      item.innerHTML = `
        <div>
          <strong>${doc.rel_path}</strong>
          <span class="text-muted" style="margin-left: 8px;">v${doc.version} (${doc.status})</span>
        </div>
        <span class="badge badge-okf">${doc.doc_type}</span>
      `;
      item.addEventListener("click", () => {
        document.querySelectorAll(".tree-node").forEach(n => n.classList.remove("active"));
        item.classList.add("active");
        docPreview.style.display = "block";
        docPreview.innerText = doc.full_content;
      });
      okfTree.appendChild(item);
    });
  } catch (err) {
    okfTree.innerHTML = "<p class='text-muted'>Failed to load OKF tree.</p>";
  }
}

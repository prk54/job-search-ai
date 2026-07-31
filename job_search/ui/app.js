// app.js — Frontend Application Logic

document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    loadDashboardStatus();
    loadProfileData();
    loadCompaniesData();
    loadJobsData();
});

// 1. Tab Navigation
function initTabNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const panes = document.querySelectorAll(".tab-pane");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            navButtons.forEach(b => b.classList.remove("active"));
            panes.forEach(p => p.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");
        });
    });
}

// 2. Toast Notifications
function showToast(message, type = "info") {
    const toast = document.getElementById("toast");
    toast.innerText = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.className = "toast";
    }, 4000);
}

// 3. Load Dashboard Statistics
async function loadDashboardStatus() {
    try {
        const res = await fetch("/api/status");
        if (!res.ok) throw new Error("Failed to fetch status");
        
        const data = await res.json();
        
        // Populate cards
        document.getElementById("stat-wishlist").innerText = data.funnel.wishlist;
        document.getElementById("stat-tailored").innerText = data.funnel.tailored;
        document.getElementById("stat-applied").innerText = data.funnel.applied;
        document.getElementById("stat-interviewing").innerText = data.funnel.interviewing;
        
        // Metadata
        document.getElementById("llm-provider-display").innerText = `Subprocess: ${data.config.llm_provider}`;
        document.getElementById("dashboard-target-subtitle").innerText = 
            `${data.config.city} • Target: ${data.config.tc_target}`;
            
        // Toggle view pdf button on profile
        const viewBaseBtn = document.getElementById("btn-view-base-pdf");
        if (data.profile_exists) {
            viewBaseBtn.disabled = false;
            viewBaseBtn.onclick = () => {
                viewPdf("base-resume.pdf", "~/.job-search/output/base-resume.pdf");
            };
        } else {
            viewBaseBtn.disabled = true;
        }
    } catch (e) {
        showToast("Error updating dashboard statistics", "error");
    }
}

// 4. Profile Management
async function loadProfileData() {
    try {
        const res = await fetch("/api/profile");
        if (res.status === 404) return; // No profile seeded yet
        if (!res.ok) throw new Error("Failed to fetch profile");
        
        const profile = await res.json();
        
        document.getElementById("prof-name").value = profile.name || "";
        document.getElementById("prof-email").value = profile.email || "";
        document.getElementById("prof-phone").value = profile.phone || "";
        document.getElementById("prof-location").value = profile.location || "";
        document.getElementById("prof-linkedin").value = profile.linkedin || "";
        document.getElementById("prof-github").value = profile.github || "";
        document.getElementById("prof-summary").value = profile.summary || "";
        
        // Store existing experience/education for submissions
        window.rawExperience = profile.experience || [];
        window.rawEducation = profile.education || [];
        window.rawSkills = profile.skills || {};
    } catch (e) {
        console.error(e);
    }
}

async function saveProfileData() {
    const payload = {
        name: document.getElementById("prof-name").value,
        email: document.getElementById("prof-email").value,
        phone: document.getElementById("prof-phone").value,
        location: document.getElementById("prof-location").value,
        linkedin: document.getElementById("prof-linkedin").value,
        github: document.getElementById("prof-github").value,
        summary: document.getElementById("prof-summary").value,
        experience: window.rawExperience || [],
        education: window.rawEducation || [],
        skills: window.rawSkills || { languages: [], frameworks_and_tools: [], databases: [] }
    };
    
    if (!payload.name || !payload.email) {
        showToast("Name and Email are required.", "error");
        return;
    }
    
    try {
        const res = await fetch("/api/profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            showToast("Base profile successfully saved and compiled!", "success");
            loadDashboardStatus();
        } else {
            showToast("Failed to save profile.", "error");
        }
    } catch (e) {
        showToast("Server error saving profile", "error");
    }
}

// 5. Target Companies Table
async function loadCompaniesData() {
    try {
        const res = await fetch("/api/companies");
        if (!res.ok) throw new Error("Failed to fetch companies");
        
        const companies = await res.json();
        const tbody = document.querySelector("#companies-table tbody");
        tbody.innerHTML = "";
        
        companies.forEach(c => {
            const tr = document.createElement("tr");
            const source = c.is_discovered ? "Discovered" : "Seed List";
            tr.innerHTML = `
                <td><strong>${c.name}</strong></td>
                <td><a href="${c.careers_url}" target="_blank" class="job-link">${c.careers_url}</a></td>
                <td><span class="badge">${c.api_type || "crawler"}</span></td>
                <td><code>${c.api_slug || "N/A"}</code></td>
                <td>T${c.tier}</td>
                <td>${source}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

async function triggerDiscovery() {
    showToast("Starting target company discovery process...", "info");
    try {
        const res = await fetch("/api/discover", { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            showToast(`Discovery complete! Added ${data.added} new companies.`, "success");
            loadCompaniesData();
            loadDashboardStatus();
        } else {
            showToast("Discovery failed.", "error");
        }
    } catch (e) {
        showToast("Error triggering discovery", "error");
    }
}

// 6. Matching Roles & Active Funnel
async function loadJobsData() {
    try {
        const res = await fetch("/api/jobs");
        if (!res.ok) throw new Error("Failed to fetch jobs");
        
        const jobs = await res.json();
        
        // Update Funnel Table
        const tbody = document.querySelector("#dashboard-jobs-table tbody");
        tbody.innerHTML = "";
        
        // Update feed count badge
        document.getElementById("jobs-funnel-badge").innerText = `${jobs.length} Positions`;
        
        jobs.forEach(j => {
            const tr = document.createElement("tr");
            
            // Score color
            const scoreVal = j.fit_score || 50;
            const fitClass = j.fit_rating === "High" ? "fit-high" : j.fit_rating === "Medium" ? "fit-medium" : "fit-low";
            
            // Resume PDF link
            let filesCell = `<span class="helper-text">None</span>`;
            if (j.tailored_resume_path) {
                const pdfName = j.tailored_resume_path.split("/").pop();
                filesCell = `<button class="btn btn-secondary btn-sm" onclick="viewPdf('${pdfName}', '${j.tailored_resume_path.replace(/\\/g, '/')}')"><i class="fa-solid fa-file-pdf"></i> Resume</button>`;
            }
            
            tr.innerHTML = `
                <td><strong>${j.company_name}</strong></td>
                <td><a href="${j.jd_url}" target="_blank" class="job-link">${j.role_title}</a></td>
                <td><span class="fit-chip ${fitClass}">${scoreVal}% (${j.fit_rating})</span></td>
                <td><span class="status-tag ${j.status}">${j.status}</span></td>
                <td>${filesCell}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="tailorResume(${j.id})">Tailor</button>
                    <button class="btn btn-secondary btn-sm" onclick="applyForm(${j.id})">Apply</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Render Feed Feed Tab
        const feed = document.getElementById("roles-feed-list");
        feed.innerHTML = "";
        
        if (jobs.length === 0) {
            feed.innerHTML = `<div class="content-card text-center"><p class="helper-text">No matching positions found. Run 'Scan Boards' to pull active listings.</p></div>`;
            return;
        }
        
        jobs.forEach(j => {
            const card = document.createElement("div");
            card.className = "job-card";
            
            const fitClass = j.fit_rating === "High" ? "fit-high" : j.fit_rating === "Medium" ? "fit-medium" : "fit-low";
            
            let filesHtml = "";
            if (j.tailored_resume_path) {
                filesHtml += `<span class="badge" style="cursor:pointer;" onclick="viewPdf('Resume', '${j.tailored_resume_path}')"><i class="fa-solid fa-file-pdf"></i> Tailored Resume</span> `;
            }
            if (j.tailored_cover_path) {
                filesHtml += `<span class="badge" style="cursor:pointer;" onclick="viewPdf('Cover Letter', '${j.tailored_cover_path}')"><i class="fa-solid fa-file-pdf"></i> Cover Letter</span>`;
            }
            
            card.innerHTML = `
                <div class="job-card-details">
                    <h3>${j.role_title}</h3>
                    <div class="job-meta-row">
                        <span><i class="fa-solid fa-building"></i> <strong>${j.company_name}</strong></span>
                        <span><i class="fa-solid fa-tag"></i> <span class="status-tag ${j.status}">${j.status}</span></span>
                        <span><i class="fa-solid fa-link"></i> <a href="${j.jd_url}" target="_blank" class="job-link">View Board Posting</a></span>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <span class="fit-chip ${fitClass}">Compatibility score: ${j.fit_score}% (${j.fit_rating})</span>
                    </div>
                    <div class="job-files-display">
                        ${filesHtml}
                    </div>
                </div>
                <div class="job-card-actions">
                    <button class="btn btn-primary" onclick="tailorResume(${j.id})"><i class="fa-solid fa-file-pen"></i> Tailor Resume</button>
                    <button class="btn btn-accent" onclick="generateCover(${j.id})"><i class="fa-solid fa-envelope-open-text"></i> Draft Cover</button>
                    <button class="btn btn-secondary" onclick="applyForm(${j.id})"><i class="fa-solid fa-arrow-up-right-from-square"></i> Auto-Apply Form</button>
                </div>
            `;
            feed.appendChild(card);
        });
        
    } catch (e) {
        console.error(e);
    }
}

async function triggerScan() {
    showToast("Scanning target boards for open roles matching keywords...", "info");
    try {
        const res = await fetch("/api/scan", { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            showToast(`Scan complete! Found ${data.jobs_found} matching roles.`, "success");
            loadJobsData();
            loadDashboardStatus();
        } else {
            showToast("Scan failed.", "error");
        }
    } catch (e) {
        showToast("Error executing board scans", "error");
    }
}

// 7. Core Application Tasks
async function tailorResume(id) {
    showToast("Launching subprocess LLM to rewrite bullets and compiling PDF...", "info");
    try {
        const res = await fetch(`/api/jobs/${id}/tailor`, { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            showToast("Tailored PDF resume compiled successfully!", "success");
            loadJobsData();
            loadDashboardStatus();
            // Open PDF preview
            viewPdf("Tailored Resume", data.pdf_path);
        } else {
            const err = await res.json();
            showToast(`Tailoring failed: ${err.detail}`, "error");
        }
    } catch (e) {
        showToast("Error tailoring resume", "error");
    }
}

async function generateCover(id) {
    showToast("Drafting cover letter and compiling matching LaTeX styling...", "info");
    try {
        const res = await fetch(`/api/jobs/${id}/cover`, { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            showToast("Tailored cover letter compiled successfully!", "success");
            loadJobsData();
            loadDashboardStatus();
            // Open PDF
            viewPdf("Cover Letter", data.pdf_path);
        } else {
            const err = await res.json();
            showToast(`Cover letter compilation failed: ${err.detail}`, "error");
        }
    } catch (e) {
        showToast("Error compiling cover letter", "error");
    }
}

async function applyForm(id) {
    showToast("Opening Chromium Playwright browser to auto-fill form...", "info");
    try {
        const res = await fetch(`/api/jobs/${id}/apply`, { method: "POST" });
        if (res.ok) {
            showToast("Playwright browser launched. Please review and click submit.", "success");
            // Reload status after browser exits (approximated)
            setTimeout(() => {
                loadJobsData();
                loadDashboardStatus();
            }, 5000);
        } else {
            showToast("Failed to launch form automation.", "error");
        }
    } catch (e) {
        showToast("Error executing application script", "error");
    }
}

// 8. PDF Preview Modal Controls
function viewPdf(title, absolutePath) {
    const modal = document.getElementById("pdf-modal");
    const titleHeader = document.getElementById("pdf-modal-title");
    const iframe = document.getElementById("pdf-iframe");
    
    titleHeader.innerText = `${title} Preview`;
    iframe.src = `/api/pdf?path=${encodeURIComponent(absolutePath)}`;
    
    modal.classList.add("active");
}

function closePdfModal() {
    const modal = document.getElementById("pdf-modal");
    const iframe = document.getElementById("pdf-iframe");
    modal.classList.remove("active");
    iframe.src = "";
}

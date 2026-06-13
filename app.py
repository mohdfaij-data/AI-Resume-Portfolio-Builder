import streamlit as st
from huggingface_hub import InferenceClient
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from io import BytesIO

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Resume Builder", page_icon="📄", layout="wide")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    .ai-output {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 0.5rem;
        white-space: pre-wrap;
    }
    .score-good { color: #16a34a; font-weight: 600; }
    .score-mid  { color: #d97706; font-weight: 600; }
    .score-low  { color: #dc2626; font-weight: 600; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── Hugging Face client ───────────────────────────────────────────────────────
client = InferenceClient(token=st.secrets["HF_TOKEN"])

def ask_ai(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {e}"

# ── Color palette ─────────────────────────────────────────────────────────────
DARK   = colors.HexColor("#1a1a2e")   # deep navy — name
ACCENT = colors.HexColor("#2563eb")   # blue — section headers
MID    = colors.HexColor("#374151")   # body text
LIGHT  = colors.HexColor("#6b7280")   # secondary / dates
RULE   = colors.HexColor("#dbeafe")   # light blue rule
BG_BAR = colors.HexColor("#eff6ff")   # skill pill background

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    name_s = ParagraphStyle("Name",
        fontName="Helvetica-Bold", fontSize=26,
        textColor=DARK, spaceAfter=2, leading=28,
        alignment=1)  # 1 = CENTER

    role_s = ParagraphStyle("Role",
        fontName="Helvetica", fontSize=12,
        textColor=ACCENT, spaceAfter=1, leading=14,
        alignment=1)  # centered

    contact_s = ParagraphStyle("Contact",
        fontName="Helvetica", fontSize=9,
        textColor=LIGHT, spaceAfter=0, leading=14,
        alignment=1)  # centered

    sec_s = ParagraphStyle("Section",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=ACCENT, spaceBefore=14, spaceAfter=3,
        leading=11, letterSpacing=1.5)

    job_title_s = ParagraphStyle("JobTitle",
        fontName="Helvetica-Bold", fontSize=11,
        textColor=DARK, spaceAfter=0, leading=14)

    org_s = ParagraphStyle("Org",
        fontName="Helvetica", fontSize=10,
        textColor=ACCENT, spaceAfter=0, leading=13)

    date_s = ParagraphStyle("Date",
        fontName="Helvetica-Oblique", fontSize=9,
        textColor=LIGHT, spaceAfter=4, leading=12)

    body_s = ParagraphStyle("Body",
        fontName="Helvetica", fontSize=10,
        textColor=MID, spaceAfter=3, leading=15)

    bullet_s = ParagraphStyle("Bullet",
        fontName="Helvetica", fontSize=10,
        textColor=MID, spaceAfter=2, leading=15,
        leftIndent=12, bulletIndent=0)

    small_s = ParagraphStyle("Small",
        fontName="Helvetica", fontSize=9,
        textColor=LIGHT, spaceAfter=2, leading=12)

    return dict(name=name_s, role=role_s, contact=contact_s,
                sec=sec_s, job_title=job_title_s, org=org_s,
                date=date_s, body=body_s, bullet=bullet_s, small=small_s)

def section_header(title, s):
    return [
        Paragraph(title.upper(), s["sec"]),
        HRFlowable(width="100%", thickness=1, color=RULE, spaceAfter=5),
    ]

# ── PDF generator ─────────────────────────────────────────────────────────────
# FIX 1: Removed the incomplete `generate_pdf` function entirely.
# FIX 2: Kept only `generate_modern_pdf` which is complete and correct.
# FIX 3: Removed duplicate imports that were embedded mid-file.
def generate_modern_pdf(data: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=12.7*mm, rightMargin=12.7*mm,
        topMargin=12*mm, bottomMargin=12*mm,
    )
    s = make_styles()
    story = []

    # ── Header block ──────────────────────────────────────────────────────────
    # Name — large bold centered, no extra space above
    story.append(Paragraph(data.get("name") or "Your Name", s["name"]))

    # Role — centered in accent colour, tight gap below name
    if data.get("role"):
        story.append(Paragraph(data["role"], s["role"]))

    # Contact — single centered line, values separated by  " · "
    # No icons, no labels above, no table — just clean plain text
    contact_parts = []
    if data.get("phone"):    contact_parts.append(data["phone"])
    if data.get("email"):    contact_parts.append(data["email"])
    if data.get("linkedin"): contact_parts.append(data["linkedin"])
    if data.get("github"):   contact_parts.append(data["github"])
    if data.get("city"):     contact_parts.append(data["city"])

    if contact_parts:
        contact_line_s = ParagraphStyle("ContactLine",
            fontName="Helvetica", fontSize=9,
            textColor=MID, leading=13, alignment=1, spaceAfter=0)
        story.append(Spacer(1, 3))
        story.append(Paragraph("  ·  ".join(contact_parts), contact_line_s))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=8))

    # ── Summary ───────────────────────────────────────────────────────────────
    if data.get("summary"):
        story += section_header("Summary", s)
        story.append(Paragraph(data["summary"], s["body"]))

    # ── Experience ────────────────────────────────────────────────────────────
    exps = [e for e in data.get("exps", []) if e.get("title")]
    if exps:
        story += section_header("Experience", s)
        for e in exps:
            story.append(Paragraph(e["title"], s["job_title"]))
            if e.get("company"):
                story.append(Paragraph(e["company"], s["org"]))
            date_str = ""
            if e.get("from"): date_str = e["from"]
            if e.get("to"):   date_str += f" – {e['to']}"
            if date_str:
                story.append(Paragraph(date_str, s["date"]))
            if e.get("desc"):
                for line in e["desc"].split("\n"):
                    line = line.strip()
                    if not line: continue
                    if line.startswith("•"):
                        story.append(Paragraph(line, s["bullet"]))
                    else:
                        story.append(Paragraph(f"• {line}", s["bullet"]))
            story.append(Spacer(1, 5))

    # ── Projects ──────────────────────────────────────────────────────────────
    projs = [p for p in data.get("projs", []) if p.get("name")]
    if projs:
        story += section_header("Projects", s)
        for p in projs:
            header = p["name"]
            if p.get("tech"): header += f"  —  {p['tech']}"
            story.append(Paragraph(header, s["job_title"]))
            if p.get("url"):
                story.append(Paragraph(p["url"], s["small"]))
            if p.get("desc"):
                story.append(Paragraph(p["desc"], s["body"]))
            story.append(Spacer(1, 5))

    # ── Education ─────────────────────────────────────────────────────────────
    edus = [e for e in data.get("edus", []) if e.get("degree")]
    if edus:
        story += section_header("Education", s)
        for e in edus:
            story.append(Paragraph(e["degree"], s["job_title"]))
            org_line = e.get("school", "")
            if e.get("year"): org_line += f"  |  {e['year']}"
            if e.get("gpa"):  org_line += f"  |  {e['gpa']}"
            if org_line:
                story.append(Paragraph(org_line, s["small"]))
            story.append(Spacer(1, 5))

    # ── Skills ────────────────────────────────────────────────────────────────
    skills = data.get("skills_list", [])
    if skills:
        story += section_header("Skills", s)
        pill_style = ParagraphStyle("Pill",
            fontName="Helvetica", fontSize=9,
            textColor=ACCENT, leading=12)
        row_size = 5
        rows = [skills[i:i+row_size] for i in range(0, len(skills), row_size)]
        for row in rows:
            cells = [Paragraph(sk, pill_style) for sk in row]
            while len(cells) < row_size:
                cells.append(Paragraph("", pill_style))
            t = Table([cells], colWidths=[34*mm]*row_size)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BG_BAR),
                ("BOX",        (0, 0), (-1, -1), 0.3, RULE),
                ("INNERGRID",  (0, 0), (-1, -1), 0.3, RULE),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
                ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(t)
            story.append(Spacer(1, 4))

    # ── Languages ─────────────────────────────────────────────────────────────
    if data.get("langs"):
        story += section_header("Languages", s)
        story.append(Paragraph(data["langs"], s["body"]))

    # ── Certifications ────────────────────────────────────────────────────────
    if data.get("certs"):
        story += section_header("Certifications", s)
        for line in data["certs"].split("\n"):
            if line.strip():
                story.append(Paragraph(f"• {line.strip()}", s["bullet"]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ── Session state defaults ────────────────────────────────────────────────────
defaults = {
    "summary_ai": "", "cover_ai": "", "linkedin_ai": "",
    "coach_reply": "", "skill_suggestions": "", "exp_polished": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header"><h1>📄 AI Resume & Portfolio Builder</h1>'
    '<p style="color:#6b7280">Fill in your details — AI polishes every section into recruiter-ready language.</p></div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["👤 Profile", "💼 Experience & Projects", "🎓 Education & Skills", "👁️ Preview & Export"]
)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Profile
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Personal information")
        fname      = st.text_input("Full name",          placeholder="e.g. Mohd Faij",                key="fname")
        femail     = st.text_input("Email",              placeholder="mohdfaij.data@email.com",        key="femail")
        fphone     = st.text_input("Phone",              placeholder="+91 73071 24699",                key="fphone")
        fcity      = st.text_input("City / location",    placeholder="Lucknow, India",                 key="fcity")
        flinkedin  = st.text_input("LinkedIn URL",       placeholder="linkedin.com/in/mohdfaij-data",  key="flinkedin")
        fportfolio = st.text_input("Portfolio / GitHub", placeholder="github.com/mohdfaij-data",       key="fportfolio")

    with col2:
        st.subheader("AI summary generator")
        frole   = st.text_input("Your current role / title", placeholder="e.g. Data Analyst",         key="frole")
        fyears  = st.selectbox("Years of experience",
                               ["0–1 years (fresher)", "1–3 years", "3–5 years", "5–10 years", "10+ years"],
                               key="fyears")
        ftarget  = st.text_input("Target job title", placeholder="e.g. Data Scientist",               key="ftarget")
        fachieve = st.text_area("Key achievements (optional)",
                                placeholder="e.g. Built product used by 10k users, reduced load time by 40%",
                                height=100, key="fachieve")

        if st.button("✨ Generate professional summary", use_container_width=True):
            with st.spinner("Writing your summary..."):
                prompt = (
                    f"Write a professional resume summary (3–4 sentences, first person, present tense, no fluff) "
                    f"for a {frole or 'professional'} with {fyears} of experience targeting a "
                    f"{ftarget or 'similar'} role. Key achievements: {fachieve or 'not specified'}. "
                    "Make it punchy, results-oriented, and ATS-friendly. Output ONLY the summary text."
                )
                st.session_state.summary_ai = ask_ai(prompt)

        if st.session_state.summary_ai:
            st.markdown("**Generated summary** — edit if needed:")
            st.session_state.summary_ai = st.text_area(
                "summary_edit", st.session_state.summary_ai,
                height=130, label_visibility="collapsed",
            )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — Experience & Projects
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Work experience")
    num_exp = st.number_input("How many positions?", 0, 6, 1, key="num_exp")
    exps = []
    for i in range(int(num_exp)):
        with st.expander(f"Position {i+1}", expanded=(i == 0)):
            c1, c2 = st.columns(2)
            title   = c1.text_input("Job title", key=f"etitle{i}", placeholder="Software engineer")
            company = c2.text_input("Company",   key=f"ecomp{i}",  placeholder="Infosys")
            c3, c4  = st.columns(2)
            efrom   = c3.text_input("From", key=f"efrom{i}", placeholder="Jan 2022")
            eto     = c4.text_input("To",   key=f"eto{i}",   placeholder="Present")
            desc    = st.text_area("Description (raw bullet points or prose)", key=f"edesc{i}",
                                   placeholder="What did you build, lead, or achieve? Include metrics.", height=100)

            col_btn, col_out = st.columns([1, 2])
            if col_btn.button("✨ Polish with AI", key=f"epol{i}"):
                with st.spinner("Polishing..."):
                    prompt = (
                        f"Rewrite this job description into 3–4 strong bullet points using action verbs "
                        f"and quantifiable metrics where possible.\nRole: {title}, Company: {company}.\n"
                        f'Raw description: "{desc}"\nOutput ONLY the bullet points starting with •.'
                    )
                    st.session_state.exp_polished[i] = ask_ai(prompt)

            polished = st.session_state.exp_polished.get(i, "")
            if polished:
                col_out.markdown("**Polished version:**")
                col_out.code(polished, language=None)

            exps.append({"title": title, "company": company, "from": efrom,
                         "to": eto, "desc": st.session_state.exp_polished.get(i, desc)})

    st.divider()
    st.subheader("Projects")
    num_proj = st.number_input("How many projects?", 0, 6, 1, key="num_proj")
    projs = []
    for i in range(int(num_proj)):
        with st.expander(f"Project {i+1}", expanded=(i == 0)):
            c1, c2 = st.columns(2)
            pname = c1.text_input("Project name", key=f"pname{i}", placeholder="Task manager app")
            ptech = c2.text_input("Tech stack",   key=f"ptech{i}", placeholder="React, Node, MongoDB")
            pdesc = st.text_area("Description & impact", key=f"pdesc{i}",
                                 placeholder="What problem did it solve? Who uses it? Any numbers?", height=80)
            purl  = st.text_input("URL (optional)", key=f"purl{i}", placeholder="github.com/...")
            projs.append({"name": pname, "tech": ptech, "desc": pdesc, "url": purl})

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — Education & Skills
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Education")
        num_edu = st.number_input("How many entries?", 0, 4, 1, key="num_edu")
        edus = []
        for i in range(int(num_edu)):
            with st.expander(f"Education {i+1}", expanded=(i == 0)):
                degree = st.text_input("Degree / course", key=f"deg{i}", placeholder="B.Tech in Computer Science")
                c1e, c2e = st.columns(2)
                school = c1e.text_input("University / school", key=f"sch{i}", placeholder="IIT Kanpur")
                eyear  = c2e.text_input("Graduation year",     key=f"eyr{i}", placeholder="2023")
                egpa   = st.text_input("GPA / % (optional)",   key=f"egpa{i}", placeholder="8.7 / 10")
                edus.append({"degree": degree, "school": school, "year": eyear, "gpa": egpa})

    with col2:
        st.subheader("Skills & tools")
        fskills = st.text_area("Technical skills (comma-separated)",
                               placeholder="Python, React, SQL, Docker, AWS", height=80, key="fskills")
        flangs  = st.text_area("Languages spoken", placeholder="English, Hindi, Tamil", height=60, key="flangs")
        fcerts  = st.text_area("Certifications",
                               placeholder="AWS Certified Solutions Architect (2024)", height=80, key="fcerts")

        if st.button("✨ Suggest skills for my role", use_container_width=True):
            with st.spinner("Finding relevant skills..."):
                prompt = (
                    f"List 15 in-demand skills and tools for a {frole or 'software developer'} "
                    f"targeting {ftarget or 'tech roles'} in 2024. "
                    "Format: comma-separated list only, no explanation, no numbering."
                )
                st.session_state.skill_suggestions = ask_ai(prompt)

        if st.session_state.skill_suggestions:
            st.info(f"💡 Suggested skills:\n{st.session_state.skill_suggestions}")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — Preview & Export
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    skills_list   = [s.strip() for s in fskills.split(",") if s.strip()] if fskills else []
    contact_parts = [x for x in [femail, fphone, fcity, flinkedin, fportfolio] if x]

    # ── Resume score ──────────────────────────────────────────────────────────
    score_items = {
        "Name & contact": 100 if fname and femail else (50 if fname or femail else 0),
        "Summary":        100 if len(st.session_state.summary_ai) > 60 else (50 if st.session_state.summary_ai else 0),
        "Experience":     100 if len([e for e in exps if e["title"] and e["desc"]]) >= 2 else (50 if exps else 0),
        "Skills":         min(100, int(len(skills_list) / 8 * 100)),
        "Education":      100 if edus and edus[0]["degree"] else 0,
        "Projects":       100 if len([p for p in projs if p["name"]]) >= 2 else (50 if projs else 0),
    }
    total_score = int(sum(score_items.values()) / len(score_items))
    score_color = "score-good" if total_score >= 75 else "score-mid" if total_score >= 40 else "score-low"

    sc1, sc2 = st.columns([1, 3])
    sc1.markdown(
        f'<p style="font-size:2.5rem;font-weight:700;text-align:center" class="{score_color}">{total_score}%</p>'
        '<p style="text-align:center;color:#6b7280;font-size:0.85rem">Resume score</p>',
        unsafe_allow_html=True,
    )
    with sc2:
        for label, val in score_items.items():
            color = "#16a34a" if val == 100 else "#d97706" if val >= 50 else "#dc2626"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'<span style="width:130px;font-size:13px;color:#6b7280">{label}</span>'
                f'<div style="flex:1;background:#e5e7eb;border-radius:4px;height:7px">'
                f'<div style="width:{val}%;background:{color};height:7px;border-radius:4px"></div></div>'
                f'<span style="font-size:13px;color:{color};width:36px">{val}%</span></div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Resume preview ────────────────────────────────────────────────────────
    st.subheader("📄 Resume preview")
    resume_lines = [f"# {fname or 'Your Name'}"]
    if frole:
        resume_lines.append(f"*{frole}*")
    if contact_parts:
        resume_lines.append(" · ".join(contact_parts))
    resume_lines.append("---")
    if st.session_state.summary_ai:
        resume_lines += ["## Summary", st.session_state.summary_ai]
    if any(e["title"] for e in exps):
        resume_lines.append("## Experience")
        for e in exps:
            if e["title"]:
                resume_lines.append(f"**{e['title']}** at {e['company']}  |  {e['from']} – {e['to']}")
                if e["desc"]:
                    resume_lines.append(e["desc"])
                resume_lines.append("")
    if any(p["name"] for p in projs):
        resume_lines.append("## Projects")
        for p in projs:
            if p["name"]:
                line = f"**{p['name']}** — {p['tech']}"
                if p["url"]:
                    line += f" | [{p['url']}]({p['url']})"
                resume_lines.append(line)
                if p["desc"]:
                    resume_lines.append(p["desc"])
                resume_lines.append("")
    if edus and edus[0]["degree"]:
        resume_lines.append("## Education")
        for e in edus:
            if e["degree"]:
                line = f"**{e['degree']}** — {e['school']}  |  {e['year']}"
                if e["gpa"]:
                    line += f"  |  {e['gpa']}"
                resume_lines.append(line)
    if skills_list:
        resume_lines += ["## Skills", ", ".join(skills_list)]
    if flangs:
        resume_lines += ["## Languages", flangs]
    if fcerts:
        resume_lines += ["## Certifications", fcerts]

    resume_text = "\n\n".join(resume_lines)
    st.markdown(resume_text)

    st.divider()

    # ── Download buttons ──────────────────────────────────────────────────────
    dl1, dl2 = st.columns(2)

    # TXT download
    dl1.download_button(
        "⬇️ Download as .txt",
        data=resume_text,
        file_name=f"{(fname or 'resume').replace(' ', '_')}_resume.txt",
        mime="text/plain",
        use_container_width=True,
    )

    # FIX 4: Call generate_modern_pdf (the complete function) instead of the
    # broken generate_pdf. Pass data as a dict matching what the function expects.
    # FIX 5: Pass the BytesIO object directly — do NOT call it as pdf_buffer().
    # Read contact info directly from session_state keys (set by keyed widgets)
    _name     = st.session_state.get("fname", "")
    _role     = st.session_state.get("frole", "")
    _email    = st.session_state.get("femail", "")
    _phone    = st.session_state.get("fphone", "")
    _city     = st.session_state.get("fcity", "")
    _linkedin = st.session_state.get("flinkedin", "")
    _github   = st.session_state.get("fportfolio", "")

    pdf_data = generate_modern_pdf({
        "name":        _name,
        "role":        _role,
        "email":       _email,
        "phone":       _phone,
        "city":        _city,
        "linkedin":    _linkedin,
        "github":      _github,
        "summary":     st.session_state.summary_ai,
        "exps":        exps,
        "projs":       projs,
        "edus":        edus,
        "skills_list": skills_list,
        "langs":       st.session_state.get("flangs", flangs),
        "certs":       st.session_state.get("fcerts", fcerts),
    })

    dl2.download_button(
        "📄 Download as PDF",
        data=pdf_data,                   # BytesIO object, not pdf_data()
        file_name=f"{(fname or 'resume').replace(' ', '_')}_resume.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.divider()

    # ── Cover letter ──────────────────────────────────────────────────────────
    st.subheader("✉️ Cover letter")
    col_cov1, col_cov2 = st.columns([1, 2])
    company_name = col_cov1.text_input("Target company (optional)", placeholder="Google")
    if col_cov1.button("✨ Generate cover letter", use_container_width=True):
        with st.spinner("Writing cover letter..."):
            prompt = (
                f"Write a professional cover letter (3 paragraphs, ~200 words) for {fname or 'the applicant'}, "
                f"a {frole or 'professional'} with {fyears} of experience applying for a {ftarget or 'similar'} role"
                f"{' at ' + company_name if company_name else ''}. "
                f"Highlight skills: {', '.join(skills_list) or 'technical skills'}. "
                "Keep it confident, human, and specific. Output ONLY the letter body, no date/address headers."
            )
            st.session_state.cover_ai = ask_ai(prompt)

    if st.session_state.cover_ai:
        col_cov2.text_area("Cover letter (editable):", st.session_state.cover_ai, height=200)
        col_cov2.download_button(
            "⬇️ Download cover letter",
            data=st.session_state.cover_ai,
            file_name="cover_letter.txt",
            mime="text/plain",
        )

    st.divider()

    # ── LinkedIn summary ──────────────────────────────────────────────────────
    st.subheader("🔗 LinkedIn summary")
    col_li1, col_li2 = st.columns([1, 2])
    if col_li1.button("✨ Generate LinkedIn summary", use_container_width=True):
        with st.spinner("Writing LinkedIn summary..."):
            prompt = (
                f"Write a LinkedIn 'About' section (150–200 words, first person, warm yet professional) "
                f"for {fname or 'the person'}, a {frole or 'professional'} with {fyears} of experience. "
                f"Target: {ftarget or 'career growth'}. Key skills: {', '.join(skills_list) or 'technical skills'}. "
                "End with a call to action. Output ONLY the text."
            )
            st.session_state.linkedin_ai = ask_ai(prompt)

    if st.session_state.linkedin_ai:
        col_li2.text_area("LinkedIn summary (editable):", st.session_state.linkedin_ai, height=160)
        col_li2.download_button(
            "⬇️ Download LinkedIn summary",
            data=st.session_state.linkedin_ai,
            file_name="linkedin_summary.txt",
            mime="text/plain",
        )

    st.divider()

    # ── AI career coach ───────────────────────────────────────────────────────
    st.subheader("🤖 AI career coach")
    coach_q = st.text_input("Ask anything about your resume or job search:",
                             placeholder="e.g. Rewrite my summary for a startup role")
    if st.button("Ask coach ↗", use_container_width=False) and coach_q:
        with st.spinner("Thinking..."):
            ctx = (
                f"Context — Name: {fname}, Role: {frole}, Target: {ftarget}, "
                f"Skills: {', '.join(skills_list)}, "
                f"Experience entries: {len([e for e in exps if e['title']])}."
            )
            prompt = (
                f"You are a professional career coach and resume expert. {ctx}\n\n"
                f'User question: "{coach_q}"\n\n'
                "Give a specific, actionable answer under 200 words. "
                "If rewriting content, output the improved version directly."
            )
            st.session_state.coach_reply = ask_ai(prompt)

    if st.session_state.coach_reply:
        st.markdown(
            f'<div class="ai-output">{st.session_state.coach_reply}</div>',
            unsafe_allow_html=True,
        )
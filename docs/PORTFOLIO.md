# Portfolio kit — DocQA demo

## Upwork portfolio entry

**Title:** AI Document Q&A Bot — answers from PDF manuals with page citations

**Description (paste):**
Demo project. A chat assistant that reads PDF manuals and answers questions with citations to the exact file and page, so every answer can be checked. Hybrid search (keywords + embeddings) handles exact error codes and part numbers as well as loosely worded questions. If the answer isn't in the documents, it says so instead of guessing. Built with Python/FastAPI, Gemini (Claude-ready), and a lightweight local vector store; deployed free on Hugging Face Spaces. Works for product manuals, SOPs, HR policies, and support knowledge bases.

**Skills tags:** AI Chatbot · RAG · LLM · Python · FastAPI · Google Gemini · Claude · Vector Search · Prompt Engineering

## 3 screenshots

Window 1440×900, browser zoom 100%, light or dark mode (pick one and keep it for all three).

1. **`1-answer-with-citations.png`** — Ask "How do I descale the machine?". Capture the numbered steps with `[n]` chips and the source cards underneath showing *brewline-x2-user-manual.pdf · Page 5*. This is the hero shot.
2. **`2-error-code.png`** — Ask "My machine shows E04, what do I do?". Click the `[1]` chip so the source card glows. Shows exact-match lookup + clickable citations.
3. **`3-not-in-docs.png`** — Ask "Does it come with a milk frother?" or "What is the price?". Capture the honest "I couldn't find that in the uploaded documents" reply. Also show an uploaded second PDF in the sidebar (any public product manual you have rights to use). Shows no hallucination + multi-doc.

Save into `docs/screenshots/`. Screenshot 1 is used in the README.

## 60–90 s video script (screen recording + voice)

| Time | Screen | Say |
|---|---|---|
| 0–8 s | App open, sample manual in sidebar | "This is a document Q&A bot. It answers questions from your PDF manuals and shows exactly where each answer came from." |
| 8–25 s | Click chip "How do I descale the machine?" → answer appears | "I ask how to descale the machine. It gives the steps from the manual, and every step has a citation." |
| 25–35 s | Click `[2]` chip → card glows → click "Page 5 ↗" → PDF opens on page 5 | "Click a citation and you jump to the exact page. Your team can check every answer in one click." |
| 35–47 s | Type "Machine shows E04, help" | "Exact error codes and part numbers work too, because it combines keyword search with AI meaning search." |
| 47–58 s | Type "What does it cost?" → "couldn't find that" | "And when the answer isn't in the documents, it says so. No made-up answers." |
| 58–72 s | Drag a new PDF into Upload → status "Added … pages" → ask a question about it | "You can upload your own manuals, SOPs or policies. It's ready to answer in seconds." |
| 72–85 s | Sidebar "How it works" + model line | "Built with Python, FastAPI and Gemini or Claude, deployed for free. I can set this up on your documents, embed it on your website, or connect it to Slack or your help desk." |
| 85–90 s | Title card: name + "Demo project" | "Message me and I'll build one on your own docs." |

Recording tips: OBS or Windows `Win+Alt+R`, 1080p, hide bookmarks bar, pre-type nothing, keep the mouse slow.

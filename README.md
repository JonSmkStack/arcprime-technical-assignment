# ArcPrime Technical Assignment

Welcome, and thanks for taking the time to work on this assignment.
This exercise is designed to mimic how work happens at ArcPrime: a real-world problem, some background, and space for you to make decisions.

## Background

ArcPrime builds AI-powered tools to help in-house counsel (IC) and inventors manage patents more effectively.

Inventors often have their ideas in academic formats like papers or presentation formats like slides, usually as PDFs. They are the ones who submit invention disclosures to their company's IC. A disclosure is the starting point of the patenting process: IC reviews it to decide if the idea should move forward toward a patent.

At minimum, a disclosure contains:

- **Title** – a short name for the invention
- **Description** – what the invention is, explained in plain terms
- **Key differences** – what makes it different or novel compared to existing approaches

This assignment lowers the bar for inventors to share potential patentable ideas in a structured way, even if they start from unstructured documents.

## What to Build

Build an end-to-end system where inventors can submit PDF documents and have them automatically converted into structured disclosure records.

### Core Requirements

1. **Interface** – Build a UI for submitting documents and viewing disclosures

   - Think about what inventors need when submitting ideas
   - Consider what in-house counsel (IC) needs when reviewing submissions

2. **Backend API** – Process uploaded documents and generate disclosure records

3. **Docket Numbers** – Generate unique identifiers in the format `IDF-0001`, `IDF-0002`, etc.

   - Auto-increment based on existing disclosures in the database

4. **Information Extraction** – Extract from each PDF:

   - Title
   - Description
   - Key differences (what makes it novel)
   - Inventor names and emails

   Use any tools you prefer: AI models, NLP libraries, OCR, document parsing APIs, etc.

5. **Error Handling** – Handle cases where PDFs are invalid, corrupted, or don't contain relevant information

6. **Database** – An initial schema is provided in `db/schema.sql`. Extend it as needed to store all extracted information.

   To modify the schema, simply edit `db/schema.sql` and restart with:

   ```shell
   docker compose down -v
   docker compose up
   ```

7. **SOLUTION.md** – Document:
   - How to run the project (step-by-step)
   - Key technical decisions and trade-offs you made
   - Any assumptions about the problem or data
   - What would be required to make it production-ready (architecture, security, scale, reliability, etc.)

### Think Like a User

As you build, consider the workflow from both perspectives:

- **Inventors**: What would make it easy and fast for them to submit ideas?
- **In-house Counsel**: What features would help them manage and review disclosures?

Feel free to add features or improvements you think would benefit these users.

### Out of scope

- Database migrations
- UI design and styling
- Test coverage

## What We Provide

This repo includes:

- Basic backend scaffolding with Express + TypeScript in `backend/`
- Basic frontend scaffolding with React + TypeScript in `frontend/`
- Docker Compose setup with PostgreSQL and predefined schema in `db/`
- Sample PDF documents in `docs/`

You're free to add libraries, modify the setup, or use different tools entirely. Use whatever approach works best for you—AI models for extraction, specific libraries for PDF parsing, or any other solutions you find appropriate.

If you use coding assistants or other AI tools during development, that's completely fine. We're interested in your architectural decisions and how you apply these tools effectively.

**Important**: Please review all code in your submission and ensure you understand what every line does. Focus on doing less with high quality rather than more with inconsistencies.

## Time Expectation

Please spend around **2 hours** on this. We respect your time, so please don't go beyond that. In the follow-up interview, we will discuss your approach, trade-offs, and what you might do with more time.

## Submission

1. Click **"Use this template"** to create your own repository
2. Implement your solution
3. Push your code to your repository (public or private)
4. Share the repository link with us

We should be able to run your solution with minimal setup using your SOLUTION.md.

## How This Works

This assignment mirrors our daily work where you get context and goals, not a rigid spec. You own the technical decisions and trade-offs, and you communicate your reasoning like you're briefing teammates.

If something is unclear, feel free to ask questions. If you need to make assumptions to move forward, use your best judgment and document your reasoning in the SOLUTION.md.

Good luck — we look forward to seeing what you build.

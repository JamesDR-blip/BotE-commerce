\# ROLE



You are a Principal Software Architect, Senior AI Engineer, and Python Backend Engineer.



Your mission is to transform this project into a production-ready AI Data Studio Platform.



DO NOT rewrite everything from scratch.



Always refactor incrementally while preserving existing functionality.



The project must remain runnable after every change.



\---



\# PROJECT VISION



Build a scalable AI Data Studio capable of solving most freelance data-processing tasks automatically.



Example user requests:



\- Clean product data

\- Validate data quality

\- Extract Brand, Model, Color, Size...

\- Normalize product titles

\- Map data between Amazon, Shopee, Lazada, Shopify...

\- Generate reports

\- Explain validation errors

\- Suggest fixes

\- Batch process thousands of files



The workflow should NOT be hardcoded.



The system must dynamically build workflows according to user requests.



\---



\# CORE PRINCIPLES



Follow:



\- SOLID

\- Clean Architecture

\- Domain Driven Design where appropriate

\- Dependency Injection

\- Plugin Architecture

\- Strong typing

\- Small reusable modules

\- Production quality code

\- Comprehensive documentation



Avoid:



\- Huge files

\- Global state

\- Code duplication

\- Unsafe exec()

\- Business logic inside API routes



\---



\# TARGET ARCHITECTURE



app/



&#x20;   main.py



agents/



&#x20;   planner.py



&#x20;   requirement\_agent.py



&#x20;   file\_inspector.py



&#x20;   schema\_detector.py



&#x20;   category\_classifier.py



&#x20;   rule\_retriever.py



&#x20;   cleaning\_agent.py



&#x20;   extraction\_agent.py



&#x20;   mapping\_agent.py



&#x20;   validation\_agent.py



&#x20;   autofix\_agent.py



&#x20;   duplicate\_agent.py



&#x20;   qa\_agent.py



&#x20;   report\_agent.py



&#x20;   delivery\_agent.py



&#x20;   memory\_agent.py



validators/



&#x20;   base.py



&#x20;   fashion.py



&#x20;   cosmetics.py



&#x20;   electronics.py



&#x20;   ...



plugins/



&#x20;   amazon/



&#x20;   shopee/



&#x20;   lazada/



&#x20;   shopify/



&#x20;   ...



services/



repositories/



database/



schemas/



configs/



reports/



api/



dashboard/



tests/



docs/



\---



\# MULTI AGENT DESIGN



Planner Agent



\- Understand user request

\- Decide workflow



Requirement Agent



\- Detect requested task



File Inspector



\- Read CSV

\- Excel

\- JSON

\- XML

\- HTML

\- PDF



Schema Detector



\- Detect columns

\- Detect data types

\- Suggest mappings



Category Classifier



\- Detect industry



Rule Retriever



\- Load YAML rules

\- Future RAG support



Cleaning Agent



\- Normalize

\- Clean

\- Standardize



Extraction Agent



Extract:



\- Brand

\- Model

\- Color

\- Size

\- Material

\- Capacity

\- Voltage

\- Weight

\- SKU

\- UPC

\- GTIN



Mapping Agent



Convert schemas between ecommerce platforms.



Validation Agent



Validate



\- Required fields

\- Formats

\- Business rules

\- Missing values

\- Duplicate values



Auto Fix Agent



Automatically fix common issues.



Duplicate Agent



Detect



\- Exact duplicates



\- Fuzzy duplicates



\- Semantic duplicates



QA Agent



Calculate



\- Completeness



\- Consistency



\- Accuracy



\- Validity



\- Duplicate rate



Generate Health Score.



Report Agent



Generate



\- HTML



\- PDF



\- Excel



\- JSON



Delivery Agent



Export



\- Local



\- API



\- Google Drive



\- S3



Memory Agent



Store



\- Validation history



\- Rules



\- Previous reports



\- User preferences



\---



\# RULE ENGINE



Support unlimited categories.



Rules must come from YAML.



Validators must load dynamically.



No hardcoded categories.



\---



\# AI LAYER



LLM must ONLY be used for:



\- category classification



\- explaining validation errors



\- suggesting fixes



\- report summarization



\- attribute extraction



\- schema mapping



Never execute generated Python code.



\---



\# PLUGIN SYSTEM



Support plugins.



Each plugin should register:



\- validators



\- mappings



\- extractors



\- exporters



Plugins should be discovered automatically.



\---



\# DATABASE



Support PostgreSQL.



Store



\- execution history



\- reports



\- logs



\- health scores



\- users



\- workflows



\---



\# API



Build FastAPI.



Endpoints:



POST /upload



POST /clean



POST /extract



POST /validate



POST /mapping



GET /history



GET /report/{id}



GET /rules



POST /chat



\---



\# DASHBOARD



Prepare backend for:



Streamlit first.



React later.



Dashboard includes:



Upload



History



Charts



Reports



Downloads



Health Score



Logs



\---



\# REPORTS



Generate:



HTML



Excel



CSV



JSON



PDF



Charts



Summary



AI explanation



\---



\# SECURITY



Never execute arbitrary code.



Validate uploads.



Prevent path traversal.



Prevent formula injection.



Prevent malicious files.



\---



\# PERFORMANCE



Support



Parallel processing



Async tasks



Caching



Streaming large files



Batch processing



\---



\# OBSERVABILITY



Structured logging



OpenTelemetry



Metrics



Tracing



Audit logs



\---



\# TESTING



Create



Unit tests



Integration tests



End-to-end tests



\---



\# DEVOPS



Docker



Docker Compose



GitHub Actions



Pre-commit



Black



Ruff



Pytest



Coverage



\---



\# DOCUMENTATION



Generate



README



Architecture diagram



Sequence diagram



Class diagram



API documentation



Developer guide



\---



\# HOW TO WORK



Do NOT rewrite everything.



Work in small incremental steps.



For every task:



1\. Explain the reason.



2\. Show architecture changes.



3\. Modify only necessary files.



4\. Keep backward compatibility.



5\. Ensure project still runs.



6\. Add tests.



7\. Update documentation.



After each completed step, stop and wait for the next instruction.



Never make huge uncontrolled changes in one response.

Current project status:



Completed:

\- Sprint 0

\- Sprint 1

\- Sprint 2

\- Sprint 3

\- Sprint 4

\- Sprint 5



Current architecture:

\- Plugin system implemented

\- Rule engine implemented

\- Logging and Config completed

\- Validation implemented 



Next sprint:

Sprint 6 – LangGraph Foundation



Follow the same project rules.


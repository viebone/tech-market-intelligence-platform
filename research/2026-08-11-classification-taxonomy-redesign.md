---
source: stakeholder-request
date: 2026-08-11
---

Two converging inputs, captured together since they identify the same root problem from
different angles.

## 1. Real-data finding (this session, prior to the external review below)

While manually extracting Requirements Signal data for ~82 real postings (substituting for
the Gemini pipeline to make progress within today's free-tier budget), Engineer postings
averaged only 1.45 skills/posting vs Product Manager's 3.09 and Designer's 2.75. Investigated
with real queries against production data:

- ~265 of ~2,100 classified Engineer postings are Solutions Engineer/Solutions
  Architect/Customer Engineer/Support Engineer/Forward Deployed roles — pre-sales and
  customer-facing, not hands-on coding. Real requirement text: "4+ years of work experience
  in pre-sales, technical architecture, consulting, or engineering." The Engineer skill list
  (Frontend frameworks, Backend frameworks, Cloud/infrastructure, etc.) has nothing that
  could ever match this.
- 216 Engineer + 26 PM + 7 Designer postings are `track=management`, scored against the same
  hands-on/IC-only skill lists.

## 2. External taxonomy review (user-provided, pasted verbatim below)

> now I can assess the actual taxonomy. For the purpose of your job-market intelligence system, I'd rate it 8/10. The underlying architecture is strong, but I would change a few things before letting this become the long-term canonical data model.
>
> What is particularly strong
>
> The biggest strength is that you're normalising the market rather than trying to reproduce job titles. Keeping raw_title alongside canonical classifications is exactly the right approach. Titles are noisy; your analytics need stable dimensions.
>
> The separation:
>
> Role Category → Sub-specialization
> Seniority
> Track
>
> is also excellent. In particular, separating track from seniority solves the Lead/Principal/Manager ambiguity much better than a single hierarchical ladder would.
>
> Your other mechanism and taxonomy_version are also very good. Those two decisions make the taxonomy evolvable rather than pretending you can design the perfect taxonomy upfront.
>
> The UX-specific research in the project also supports the need to handle titles such as UX Designer, Product Designer, UX Researcher, UX/UI Designer and design-management roles rather than assuming there is one stable "UX Designer" title.
>
> The biggest issue: seniority isn't really one dimension
>
> You currently have:
>
> entry → junior → mid → senior → lead → principal → manager → director → vp → exec
>
> But that combines level and organizational role.
>
> For example:
>
> Senior Product Designer
> Lead Product Designer
> Principal Product Designer
> Design Manager
> Senior Design Manager
> Director of Product Design
> Senior Director of Product Design
> VP Design
>
> Where does Senior Design Manager go? senior or manager?
>
> The problem becomes even clearer with:
>
> Senior Engineering Manager
> Principal Engineering Manager
> Group Product Manager
> Senior Product Manager
> Director Product Management
>
> I'd therefore change this before accumulating much data.
>
> I would use something closer to:
>
> level
> entry
> junior
> mid
> senior
> lead
> principal
> director
> vp
> executive
> unknown
>
> track
> ic
> management
> unknown
>
> And let the combination represent the position:
>
> Senior Product Designer
> level = senior
> track = ic
>
> Principal Engineer
> level = principal
> track = ic
>
> Senior Engineering Manager
> level = senior
> track = management
>
> Director of Product
> level = director
> track = management
>
> You may eventually want an additional management_scope, but I wouldn't add that yet.
>
> Second issue: your Role Category is doing two jobs
>
> You define:
>
> Designer
> Product Manager
> Engineer
>
> That's perfectly reasonable for the product experience because those are the three markets you want to compare.
>
> But I wouldn't make them the fundamental ontology of a job.
>
> Internally I'd distinguish:
>
> occupation_family
> Design
> Product
> Engineering
>
> specialization
> Product Design
> UX Design
> UX Research
> UI Design
> ...
>
> Then the UI can still say:
>
> Designer
> Product Manager
> Engineer
>
> Why bother?
>
> Because eventually you'll encounter:
>
> Design Manager
> Head of Design
> Product Design Manager
> Director of UX
> VP Product
> Head of Product
> Engineering Manager
> CTO
>
> "Product Manager" becomes awkward as the parent category of VP Product.
>
> Product doesn't.
>
> Likewise Designer is an occupation, while Design is a family.
>
> So I'd make the database concept:
>
> Design / Product / Engineering
>
> while allowing the product to present them as:
>
> Designer / Product Manager / Engineer.
>
> That is a small naming change with significant long-term benefit.
>
> Your specializations need one important addition
>
> For Design you currently have:
>
> UX Designer
> UX Researcher
> Product Designer
> UI Designer
>
> I'd strongly consider:
>
> UX Designer
> Product Designer
> UX Researcher
> UI Designer
> Content Designer / UX Writer
> Design Systems
> Other Design
>
> But there's an even more important structural point: don't force every job into a specialization.
>
> A posting such as:
>
> Senior Designer – Digital Products
>
> might clearly be Design, while there isn't enough evidence to say UX vs Product vs UI.
>
> So:
>
> role_category = design
> specialization = unknown
>
> is better than guessing.
>
> That principle should apply everywhere in the taxonomy.
>
> I would explicitly introduce unknown
>
> Right now you have other, but other and unknown mean very different things.
>
> Consider:
>
> Digital Lead
>
> The classifier doesn't have enough information.
>
> Versus:
>
> Corporate Lawyer
>
> We know what it is, and it isn't one of your tracked occupations.
>
> Those should become:
>
> Digital Lead
> role_category = unknown
>
> Corporate Lawyer
> role_category = other
>
> This distinction becomes very valuable analytically.
>
> If 14% of your ingestion becomes unknown, your classifier/data source has a quality problem.
>
> If 14% becomes other, your source query has a targeting problem.
>
> Without the distinction, those two completely different problems look identical.
>
> Requirements: strong concept, but skills need another layer
>
> The requirements part is probably the weakest part of the taxonomy—not because it's wrong, but because it will become limiting fastest.
>
> For example:
>
> Engineer
> Frontend frameworks
> Backend frameworks
> Cloud/infrastructure
> Databases
> ...
>
> If a posting says:
>
> React
> TypeScript
> AWS
> PostgreSQL
> Kubernetes
>
> and you only store the categories, you'll later be unable to answer one of the most interesting market questions:
>
> "Which technologies are becoming more frequently requested?"
>
> I'd therefore store both normalized skill and skill group:
>
> raw_skill          normalized_skill       skill_group
>
> React              React                  Frontend framework
> React.js           React                  Frontend framework
> AWS                AWS                    Cloud/infrastructure
> Amazon Web Services AWS                   Cloud/infrastructure
> Figma              Figma                  Design tooling
>
> Then your market can answer both:
>
> "42% of engineering jobs request frontend-framework experience."
>
> and:
>
> "React appears in 31% of frontend roles, up from 24% last year."
>
> That second type of question is potentially one of the strongest features of your product.
>
> Education also needs one small conceptual change
>
> Your hierarchy:
>
> not_mentioned
> bootcamp_or_equivalent
> bachelors
> masters
> phd
>
> assumes one ascending requirement.
>
> Real postings say things like:
>
> Bachelor's degree or equivalent professional experience.
>
> I'd avoid interpreting that simply as bachelors.
>
> At minimum I'd capture:
>
> education_level
> education_required
> equivalent_experience_accepted
>
> Otherwise your eventual market insight:
>
> "38% of Product roles require a bachelor's degree"
>
> could be misleading if half of those explicitly accept equivalent experience.
>
> One thing I would definitely keep
>
> This rule is excellent:
>
> classify Role Category/Seniority/Track from title, but extract requirements from description.
>
> Don't let the LLM use the entire description to "improve" the occupational classification unless you explicitly introduce a fallback later.
>
> Keeping classification evidence separate from requirements evidence makes the resulting data much easier to reason about.
>
> [structure proposal and 9/10-weighted scoring table omitted here — see conversation transcript for full text; fully reflected in the agreed scope below]

## 3. Confirming evidence gathered in response (this session)

Queried real classified data to test the review's central claim before accepting it:

```
seniority distribution where track = management:
  manager: 160   senior: 32   lead: 20   director: 19   mid: 6   (null: 13)
```

All 160 `seniority=manager` rows are real, distinct titles ("Engineering Manager, Model
Flywheel," "Systems Engineering Manager," "Support Engineering Manager (APAC)") — confirming
the collapse is active and ongoing, not hypothetical. Also observed in passing: ~64% of all
classified postings (3,269 of ~5,105) have `seniority: NULL` — noted as a separate, real
finding but explicitly out of scope for this change (an extraction-rate question, not a
taxonomy-structure question).

See conversation for the full converged scope this triage should assess.

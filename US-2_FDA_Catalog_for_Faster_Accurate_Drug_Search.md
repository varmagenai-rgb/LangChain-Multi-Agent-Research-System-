# US-2 – FDA Catalog for Faster, Accurate Drug Search

## Overview
Replace broken nephrology drug search returning ~28,000 unrelated rows with clean indexed FDA catalog

## User Story
**As a** Chief Medical Officer or regulatory analyst
**I want** 'show nephrology drugs' to return only true nephrology drugs
**So that** I can trust the results and finish a drug review in one sitting

## Business Value
CMOs lose time filtering and lose trust in the system. Fixing this delivers a credible single-question demo

## Measurable Outcome
Primary_Therapeutic_Area = Nephrology returns <= 15 rows, down from ~28,000 today

## Acceptance Criteria
Filtering by Nephrology returns Kerendia and excludes dexamethasone
Searching for sponsor Pfizer matches all Pfizer entity variants
Year-range filter returns only drugs approved in that range
All 54,186 FDA labels appear in the catalog
Single filter query returns in under 100 milliseconds

## References
- [Azure Board – Work Item 2](https://dev.azure.com/GenAgenticAI/AzureBoardTest/_workitems/edit/2)

## Status
- [ ] In Progress
- [ ] In Review  
- [ ] Done

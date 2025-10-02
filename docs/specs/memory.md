# Summary
Major expansion to our mcp-jive platform:  Addition of several "memory" segments that can be used by AI Agents. Goal is to enchance agent prompts and requests by embeding relevent context from MCP jive memory. 

# instructions
Create a comprehensive initiative using MCP Jive tools which will expand our MCP Jive platform with use of Jive-memory. Initiative should be created with all the relevent sub items and all properly linked together with very detailed and comprehensive requriements. 
- During plan buildout research existing similar systems online for ideas and inspiration
- Reference existing docs and architecture guidelines and research existing codebase
- Before any implementation validate assumptions and always research several options before deciding on one. 
- Never assume that your implementation is working, always validate all of the requirements
- Create all the needed tests and make sure it is fully 100% validated

# Requirements
- Each of the capabilities listed here should be filtered and limited to individual namespaces, meaning each namespace should have separate memory for each of the memory types listed here
- All of the memory should be able to be exported (saved) as md files in same directory structure as similar work items functionality ( research how its done )
- All of the requirements, descriptions and text content should be saved and managed as Markdown formats. 
## Technology
- Should use the same LanceDB engine as current mcp-jive server
- Should expand the same combined APIs and MCP Tools

## Functionality
### Architecture Memory
Allows for storage and easy retrieval of an "Architecture Item", which is an individual piece or segment of architecture requirements. 
- Architecture Item can have children items and be linked and associated to other Architecture Items. 
- Each Architecture item can contain max of 10,000 characters but system should encourage shorter ones
- AI Agent should always be encourage to use this tool when referencing or creating any architectures or when implementing code 
- Tool that will reference these architecture items, should be smart to summarize the item, all the children and any related architecture items into a concise instructions for AI Agent. Tool should be aware of AI Agent and LLM models context limits, so should always look to return only the most important elements. 
- Tools should have abilities to retrieve individual architecture items, recursive and related architecture items, and as well as combined and concise context friendly instructions which are all based on the architecture items. 
- Existing Epic Working Items should be expanded to link and reference one or multiple architecture items
#### Attributes
Not a complete list but some of the attrubutes that should be available

UniqueSlug: Unique short max 100 charcters slug / identificaiton of architecture item
LastUpdatedOn: Date item was last updated
CreatedOn: Date item was originally created
Title: Human Friendly Short name of this architecture item
AIWhenToUse: Array List of AI Friendly instructions when architecture item should be applied
AIRequirements: AI Friendly Detailed specifications of the architecture
Keywords: Array List of keywords that describe this architecture item
ChildrenSlugs: Array List of slugs that are children of this architecture item
RelatedSlugs: Array List of slugs that are related to this architecture item

### Troubleshoot Memory
Allows for storing troubleshooting tips for AI Agents
- Each Troubleshooting item can contain max of 10,000 characters but system should encourage shorter ones
- AI Agent should always be encourage to use this tool when stuck in solving a specific problem or troubleshooting an issue. 
- Troubleshooting tips can be retrieved, updated and provides as concise context and AI Friendly instructions to help the AI solve a common problem

#### Attributes
Not a complete list but some of the attrubutes that should be available

UniqueSlug: Unique short max 100 charcters slug / identificaiton of troubleshooting item
LastUpdatedOn: Date item was last updated
CreatedOn: Date item was originally created
Title: Human Friendly Short name of this troubleshooting item
AIUseCase: Array List of AI Friendly short problem descriptions when this troubleshooting item should be applied
AISolutions: AI Friendly Solution to the problem, in form of tips, steps or instructions that AI agent should follow
Keywords: Array List of keywords that describe this troubleshooting item

### Memory UI/UX
We need to expand our existing frontend web app with two new tabs: Architecture Memory, Troubleshoot Memory.
UI/UX should follow similar style and functionality as 'Work Items' tabs. Should have capability view, create and edit.  

"""AI Guidance Generator for creating context-aware prompts and instructions.

This module provides comprehensive AI guidance generation capabilities including
prompt template creation, context-aware instruction generation, and step-by-step
guidance for AI agents executing work items.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import json

from .models import (
    AIGuidance,
    ExecutionStep,
    ExecutionPlan,
    PlanningContext,
    GuidanceType,
    InstructionDetail
)
from ..uuid_utils import generate_uuid

logger = logging.getLogger(__name__)


class AIGuidanceGenerator:
    """AI guidance generator for work item execution.
    
    Provides comprehensive guidance generation including prompt templates,
    step-by-step instructions, and context-aware AI guidance for various
    work item types and execution scenarios.
    """
    
    def __init__(self, prompts_directory: Optional[str] = None):
        """Initialize the AI guidance generator.
        
        Args:
            prompts_directory: Directory containing prompt templates
        """
        self.prompts_directory = Path(prompts_directory) if prompts_directory else None
        self.logger = logging.getLogger(__name__)
        self._template_cache = {}
    
    async def generate_execution_guidance(
        self,
        work_item: Dict[str, Any],
        context: PlanningContext,
        guidance_type: GuidanceType = GuidanceType.TACTICAL,
        instruction_detail: InstructionDetail = InstructionDetail.DETAILED
    ) -> AIGuidance:
        """Generate comprehensive AI guidance for work item execution.
        
        Args:
            work_item: Work item data
            context: Planning context
            guidance_type: Type of guidance to generate
            instruction_detail: Level of detail for instructions
            
        Returns:
            AIGuidance: Complete AI guidance package
        """
        try:
            # Generate approach based on work item characteristics
            try:
                approach = await self._generate_execution_approach(
                    work_item, context, guidance_type
                )
            except Exception as e:
                self.logger.warning(f"Error generating execution approach: {str(e)}")
                approach = f"Execute {work_item.get('item_type', 'task')}: {work_item.get('title', 'Untitled')} using standard practices."
            
            # Generate key considerations
            try:
                considerations = await self._generate_key_considerations(
                    work_item, context
                )
            except Exception as e:
                self.logger.warning(f"Error generating key considerations: {str(e)}")
                considerations = ["Follow best practices", "Ensure quality standards", "Test thoroughly"]
            
            # Generate success criteria
            try:
                success_criteria = await self._generate_success_criteria(
                    work_item, instruction_detail
                )
            except Exception as e:
                self.logger.warning(f"Error generating success criteria: {str(e)}")
                success_criteria = ["Task completed successfully", "All requirements met", "Quality standards satisfied"]
            
            # Generate best practices
            try:
                best_practices = await self._generate_best_practices(
                    work_item, context
                )
            except Exception as e:
                self.logger.warning(f"Error generating best practices: {str(e)}")
                best_practices = ["Follow coding standards", "Write comprehensive tests", "Document implementation"]
            
            # Generate common pitfalls
            try:
                common_pitfalls = await self._generate_common_pitfalls(
                    work_item, context
                )
            except Exception as e:
                self.logger.warning(f"Error generating common pitfalls: {str(e)}")
                common_pitfalls = ["Insufficient testing", "Poor error handling", "Inadequate documentation"]
            
            # Determine tools needed
            try:
                tools_needed = await self._determine_tools_needed(
                    work_item, context
                )
            except Exception as e:
                self.logger.warning(f"Error determining tools needed: {str(e)}")
                tools_needed = ["code_editor", "version_control", "testing_framework"]
            
            return AIGuidance(
                approach=approach,
                key_considerations=considerations,
                success_criteria=success_criteria,
                best_practices=best_practices,
                common_pitfalls=common_pitfalls,
                tools_needed=tools_needed,
                estimated_complexity=work_item.get("complexity", "moderate")
            )
            
        except Exception as e:
            self.logger.error(f"Error generating AI guidance: {str(e)}")
            # Return minimal fallback guidance
            return AIGuidance(
                approach=f"Execute {work_item.get('item_type', 'task')}: {work_item.get('title', 'Untitled')}",
                key_considerations=["Follow standard practices"],
                success_criteria=["Task completed successfully"],
                best_practices=["Follow coding standards"],
                common_pitfalls=["Insufficient testing"],
                tools_needed=["code_editor"],
                estimated_complexity=work_item.get("complexity", "moderate")
            )
    
    async def generate_prompt_template(
        self,
        work_item: Dict[str, Any],
        context: PlanningContext,
        template_type: str = "execution"
    ) -> str:
        """Generate AI prompt template for work item execution.
        
        Args:
            work_item: Work item data
            context: Planning context
            template_type: Type of prompt template to generate
            
        Returns:
            str: Generated prompt template
        """
        try:
            # Load base template
            base_template = await self._load_template(template_type)
            
            # Generate context-specific variables
            template_vars = await self._generate_template_variables(
                work_item, context
            )
            
            # Render template with variables
            rendered_template = await self._render_template(
                base_template, template_vars
            )
            
            return rendered_template
            
        except Exception as e:
            self.logger.error(f"Error generating prompt template: {str(e)}")
            raise
    
    async def generate_step_by_step_instructions(
        self,
        execution_plan: ExecutionPlan,
        detail_level: InstructionDetail = InstructionDetail.DETAILED
    ) -> List[Dict[str, Any]]:
        """Generate step-by-step instructions for execution plan.
        
        Args:
            execution_plan: Complete execution plan
            detail_level: Level of detail for instructions
            
        Returns:
            List[Dict[str, Any]]: Step-by-step instructions
        """
        try:
            instructions = []
            
            for i, step in enumerate(execution_plan.execution_sequence, 1):
                try:
                    instruction = await self._generate_step_instruction(
                        step, i, detail_level, execution_plan
                    )
                    instructions.append(instruction)
                except Exception as e:
                    self.logger.warning(f"Error generating instruction for step {i}: {str(e)}")
                    # Create fallback instruction
                    fallback_instruction = {
                        "step_number": i,
                        "step_id": getattr(step, 'step_id', f"step_{i}"),
                        "title": getattr(step, 'title', f"Step {i}"),
                        "description": getattr(step, 'description', "Execute this step as planned"),
                        "priority": "medium",
                        "estimated_duration": "30 minutes"
                    }
                    instructions.append(fallback_instruction)
            
            return instructions
            
        except Exception as e:
            self.logger.error(f"Error generating step instructions: {str(e)}")
            # Return minimal fallback instructions
            return [{
                "step_number": 1,
                "step_id": "fallback_step",
                "title": "Execute Work Item",
                "description": "Complete the work item according to requirements",
                "priority": "medium",
                "estimated_duration": "60 minutes"
            }]
    
    async def generate_context_aware_prompts(
        self,
        work_items: List[Dict[str, Any]],
        context: PlanningContext
    ) -> Dict[str, str]:
        """Generate context-aware prompts for multiple work items.
        
        Args:
            work_items: List of work items
            context: Planning context
            
        Returns:
            Dict[str, str]: Mapping of work item IDs to prompts
        """
        try:
            prompts = {}
            
            for work_item in work_items:
                work_item_id = work_item.get("work_item_id")
                
                # Safe conversion to avoid numpy array boolean evaluation error
                if hasattr(work_item_id, 'tolist'):
                    work_item_id = work_item_id.tolist()
                elif hasattr(work_item_id, '__iter__') and not isinstance(work_item_id, str):
                    try:
                        work_item_id = list(work_item_id)[0] if work_item_id else None
                    except Exception:
                        work_item_id = str(work_item_id) if work_item_id is not None else None
                
                if work_item_id is not None and str(work_item_id).strip():
                    prompt = await self.generate_prompt_template(
                        work_item, context
                    )
                    prompts[str(work_item_id)] = prompt
            
            return prompts
            
        except Exception as e:
            self.logger.error(f"Error generating context-aware prompts: {str(e)}")
            raise
    
    async def generate_validation_prompts(
        self,
        work_item: Dict[str, Any],
        acceptance_criteria: List[str]
    ) -> List[str]:
        """Generate validation prompts for acceptance criteria.
        
        Args:
            work_item: Work item data
            acceptance_criteria: List of acceptance criteria
            
        Returns:
            List[str]: Validation prompts
        """
        try:
            validation_prompts = []
            
            for criterion in acceptance_criteria:
                prompt = await self._generate_validation_prompt(
                    work_item, criterion
                )
                validation_prompts.append(prompt)
            
            return validation_prompts
            
        except Exception as e:
            self.logger.error(f"Error generating validation prompts: {str(e)}")
            raise
    
    # Private helper methods
    
    async def _generate_execution_approach(
        self,
        work_item: Dict[str, Any],
        context: PlanningContext,
        guidance_type: GuidanceType
    ) -> str:
        """Generate execution approach based on work item and context."""
        item_type = work_item.get("item_type", "task")
        complexity = work_item.get("complexity", "moderate")
        context_tags = work_item.get("context_tags", [])
        
        # Handle numpy arrays safely
        if hasattr(context_tags, 'tolist'):
            context_tags = context_tags.tolist()
        elif not isinstance(context_tags, list):
            # Safe handling of context_tags to avoid numpy array ambiguity
            try:
                if context_tags is not None:
                    if hasattr(context_tags, 'tolist'):
                        context_tags = context_tags.tolist()
                    context_tags = list(context_tags) if context_tags else []
                else:
                    context_tags = []
            except Exception:
                context_tags = []
        
        # Base approach templates
        approach_templates = {
            "task": {
                "simple": "Execute this task using a direct, straightforward approach. Focus on clear implementation and basic validation.",
                "moderate": "Implement this task systematically with proper planning, validation checkpoints, and comprehensive testing.",
                "complex": "Break down this complex task into manageable phases. Implement with extensive planning, risk mitigation, and thorough validation."
            },
            "epic": {
                "simple": "Coordinate execution of child features in logical sequence. Ensure integration points are validated.",
                "moderate": "Orchestrate parallel execution of features where possible. Manage dependencies and integration carefully.",
                "complex": "Execute strategic rollout with phased delivery. Implement comprehensive risk management and stakeholder communication."
            },
            "feature": {
                "simple": "Develop feature with focus on core functionality and user requirements.",
                "moderate": "Implement feature with comprehensive testing, documentation, and integration validation.",
                "complex": "Architect and implement feature with scalability, performance, and maintainability considerations."
            },
            "story": {
                "simple": "Implement user story focusing on acceptance criteria and user value delivery.",
                "moderate": "Develop user story with comprehensive testing and user experience validation.",
                "complex": "Implement user story with advanced UX considerations, performance optimization, and accessibility."
            }
        }
        
        base_approach = approach_templates.get(item_type, approach_templates["task"]).get(
            complexity, approach_templates["task"]["moderate"]
        )
        
        # Enhance based on context tags
        enhancements = []
        if self._safe_tag_check("frontend", context_tags):
            enhancements.append("Prioritize user experience, responsive design, and cross-browser compatibility.")
        if self._safe_tag_check("backend", context_tags):
            enhancements.append("Focus on scalability, performance optimization, and robust error handling.")
        if self._safe_tag_check("database", context_tags):
            enhancements.append("Ensure data integrity, optimize queries, and implement proper indexing.")
        if self._safe_tag_check("api", context_tags):
            enhancements.append("Follow REST/GraphQL best practices and implement comprehensive API documentation.")
        if self._safe_tag_check("security", context_tags):
            enhancements.append("Implement security best practices, input validation, and access controls.")
        if self._safe_tag_check("performance", context_tags):
            enhancements.append("Optimize for performance with caching, efficient algorithms, and resource management.")
        
        # Enhance based on guidance type
        if guidance_type == GuidanceType.STRATEGIC:
            enhancements.append("Consider long-term architectural implications and strategic alignment.")
        elif guidance_type == GuidanceType.TACTICAL:
            enhancements.append("Focus on immediate implementation details and tactical execution.")
        
        # Enhance based on environment
        execution_env = getattr(context, 'execution_environment', 'development')
        if execution_env == "production":
            enhancements.append("Ensure production-ready implementation with monitoring and rollback capabilities.")
        
        # Safe conversion to avoid numpy array boolean evaluation error
        if hasattr(enhancements, 'tolist'):
            enhancements = enhancements.tolist()
        elif not isinstance(enhancements, list):
            try:
                enhancements = list(enhancements) if enhancements else []
            except Exception:
                enhancements = []
        
        if len(enhancements) > 0:
            return f"{base_approach} {' '.join(enhancements)}"
        
        return base_approach
    
    async def _generate_key_considerations(
        self,
        work_item: Dict[str, Any],
        context: PlanningContext
    ) -> List[str]:
        """Generate key considerations for work item execution."""
        considerations = []
        
        # Environment-specific considerations
        env = getattr(context, 'execution_environment', 'development')
        if env == "production":
            considerations.extend([
                "Ensure zero-downtime deployment strategy",
                "Implement comprehensive monitoring and alerting",
                "Plan for immediate rollback if issues arise",
                "Validate against production data patterns"
            ])
        elif env == "staging":
            considerations.extend([
                "Test with production-like data volumes",
                "Validate integration points thoroughly",
                "Perform end-to-end testing scenarios"
            ])
        elif env == "development":
            considerations.extend([
                "Set up proper development environment",
                "Implement comprehensive unit testing",
                "Document development decisions"
            ])
        
        # Complexity-based considerations
        complexity = work_item.get("complexity", "moderate")
        if complexity == "complex":
            considerations.extend([
                "Break down into smaller, manageable components",
                "Implement comprehensive error handling and recovery",
                "Plan for multiple validation checkpoints",
                "Consider impact on existing systems",
                "Implement detailed logging and monitoring"
            ])
        elif complexity == "simple":
            considerations.extend([
                "Ensure basic validation and testing",
                "Document implementation approach",
                "Verify against acceptance criteria"
            ])
        
        # Context tag considerations
        context_tags = work_item.get("context_tags", [])
        
        # Handle numpy arrays safely
        if hasattr(context_tags, 'tolist'):
            context_tags = context_tags.tolist()
        elif not isinstance(context_tags, list):
            # Safe handling of context_tags to avoid numpy array ambiguity
            try:
                if context_tags is not None:
                    if hasattr(context_tags, 'tolist'):
                        context_tags = context_tags.tolist()
                    context_tags = list(context_tags) if context_tags else []
                else:
                    context_tags = []
            except Exception:
                context_tags = []
        
        tag_considerations = {
            "security": [
                "Implement input validation and sanitization",
                "Follow security best practices and guidelines",
                "Conduct security testing and vulnerability assessment"
            ],
            "performance": [
                "Profile and optimize critical code paths",
                "Implement appropriate caching strategies",
                "Monitor resource usage and scalability"
            ],
            "integration": [
                "Validate all integration points",
                "Implement proper error handling for external dependencies",
                "Test failure scenarios and recovery mechanisms"
            ],
            "migration": [
                "Plan for data migration and validation",
                "Implement rollback procedures",
                "Test migration process thoroughly"
            ]
        }
        
        for tag in context_tags:
            if tag in tag_considerations:
                considerations.extend(tag_considerations[tag])
        
        # Priority-based considerations
        priority = work_item.get("priority", "medium")
        if priority == "high" or priority == "critical":
            considerations.extend([
                "Prioritize quality and reliability over speed",
                "Implement additional validation and testing",
                "Ensure stakeholder communication and updates"
            ])
        
        return considerations
    
    async def _generate_success_criteria(
        self,
        work_item: Dict[str, Any],
        detail_level: InstructionDetail
    ) -> List[str]:
        """Generate success criteria for work item."""
        # Use existing acceptance criteria if available
        existing_criteria = work_item.get("acceptance_criteria", [])
        # Safe handling of existing_criteria to avoid numpy array ambiguity
        criteria_available = False
        if existing_criteria is not None:
            if hasattr(existing_criteria, 'tolist'):
                existing_criteria = existing_criteria.tolist()
                criteria_available = len(existing_criteria) > 0
            elif isinstance(existing_criteria, (list, tuple)):
                criteria_available = len(existing_criteria) > 0
            else:
                try:
                    criteria_available = len(list(existing_criteria)) > 0 if existing_criteria else False
                except Exception:
                    criteria_available = bool(existing_criteria)
        
        if criteria_available and detail_level != InstructionDetail.COMPREHENSIVE:
            return existing_criteria
        
        # Generate default criteria based on item type
        item_type = work_item.get("item_type", "task")
        complexity = work_item.get("complexity", "moderate")
        
        criteria_templates = {
            "task": {
                "simple": [
                    "Implementation meets functional requirements",
                    "Basic testing passes",
                    "Code follows established standards"
                ],
                "moderate": [
                    "All functional requirements implemented correctly",
                    "Comprehensive testing suite passes",
                    "Code review completed and approved",
                    "Documentation updated appropriately"
                ],
                "complex": [
                    "All functional and non-functional requirements met",
                    "Comprehensive testing including edge cases",
                    "Performance benchmarks achieved",
                    "Security validation completed",
                    "Integration testing passes",
                    "Documentation and runbooks updated"
                ]
            },
            "epic": {
                "simple": [
                    "All child features completed successfully",
                    "Integration testing passes",
                    "User acceptance criteria validated"
                ],
                "moderate": [
                    "All child features delivered and integrated",
                    "End-to-end testing scenarios pass",
                    "Performance requirements met",
                    "User acceptance testing completed",
                    "Documentation and training materials updated"
                ],
                "complex": [
                    "Strategic objectives achieved",
                    "All features delivered with quality standards",
                    "Comprehensive testing across all scenarios",
                    "Performance and scalability validated",
                    "Security and compliance requirements met",
                    "Stakeholder approval and sign-off obtained",
                    "Monitoring and support procedures established"
                ]
            }
        }
        
        base_criteria = criteria_templates.get(item_type, criteria_templates["task"]).get(
            complexity, criteria_templates["task"]["moderate"]
        )
        
        # Enhance with existing criteria if comprehensive detail requested
        if detail_level == InstructionDetail.COMPREHENSIVE and existing_criteria:
            return list(set(base_criteria + existing_criteria))
        
        return base_criteria
    
    async def _generate_best_practices(
        self,
        work_item: Dict[str, Any],
        context: PlanningContext
    ) -> List[str]:
        """Generate best practices for work item execution."""
        practices = [
            "Follow established coding standards and conventions",
            "Implement comprehensive testing strategy",
            "Document implementation decisions and rationale",
            "Use version control with meaningful commit messages",
            "Conduct code reviews before merging changes"
        ]
        
        # Context tag specific practices
        context_tags = work_item.get("context_tags", [])
        
        # Handle numpy arrays safely
        if hasattr(context_tags, 'tolist'):
            context_tags = context_tags.tolist()
        elif not isinstance(context_tags, list):
            # Safe handling of context_tags to avoid numpy array ambiguity
            try:
                if context_tags is not None:
                    if hasattr(context_tags, 'tolist'):
                        context_tags = context_tags.tolist()
                    context_tags = list(context_tags) if context_tags else []
                else:
                    context_tags = []
            except Exception:
                context_tags = []
        
        if self._safe_tag_check("frontend", context_tags):
            practices.extend([
                "Ensure cross-browser compatibility",
                "Optimize for mobile and responsive design",
                "Implement accessibility standards (WCAG)",
                "Optimize bundle size and loading performance",
                "Use semantic HTML and proper ARIA labels"
            ])
        
        if self._safe_tag_check("backend", context_tags):
            practices.extend([
                "Implement proper error handling and logging",
                "Use appropriate design patterns",
                "Optimize database queries and connections",
                "Implement proper caching strategies",
                "Follow API design principles (REST/GraphQL)"
            ])
        
        if self._safe_tag_check("database", context_tags):
            practices.extend([
                "Use proper indexing strategies",
                "Implement data validation and constraints",
                "Plan for data migration and backup",
                "Optimize query performance",
                "Follow database normalization principles"
            ])
        
        if self._safe_tag_check("security", context_tags):
            practices.extend([
                "Implement input validation and sanitization",
                "Use secure authentication and authorization",
                "Follow OWASP security guidelines",
                "Implement proper session management",
                "Use HTTPS and secure communication protocols"
            ])
        
        # Environment specific practices
        execution_env = getattr(context, 'execution_environment', 'development')
        if execution_env == "production":
            practices.extend([
                "Implement comprehensive monitoring and alerting",
                "Use feature flags for gradual rollouts",
                "Implement proper backup and recovery procedures",
                "Plan for zero-downtime deployments"
            ])
        
        return practices
    
    async def _generate_common_pitfalls(
        self,
        work_item: Dict[str, Any],
        context: PlanningContext
    ) -> List[str]:
        """Generate common pitfalls to avoid."""
        pitfalls = [
            "Insufficient testing coverage leading to bugs in production",
            "Poor error handling causing system instability",
            "Inadequate documentation making maintenance difficult",
            "Ignoring performance implications of implementation choices",
            "Not considering edge cases and boundary conditions"
        ]
        
        # Complexity-based pitfalls
        complexity = work_item.get("complexity", "moderate")
        if complexity == "complex":
            pitfalls.extend([
                "Underestimating integration complexity and dependencies",
                "Insufficient stakeholder communication and alignment",
                "Inadequate rollback and recovery planning",
                "Not breaking down complex tasks into manageable pieces",
                "Overlooking non-functional requirements"
            ])
        
        # Context tag specific pitfalls
        context_tags = work_item.get("context_tags", [])
        
        # Handle numpy arrays safely
        if hasattr(context_tags, 'tolist'):
            context_tags = context_tags.tolist()
        elif not isinstance(context_tags, list):
            # Safe handling of context_tags to avoid numpy array ambiguity
            try:
                if context_tags is not None:
                    if hasattr(context_tags, 'tolist'):
                        context_tags = context_tags.tolist()
                    context_tags = list(context_tags) if context_tags else []
                else:
                    context_tags = []
            except Exception:
                context_tags = []
        
        if self._safe_tag_check("frontend", context_tags):
            pitfalls.extend([
                "Not testing across different browsers and devices",
                "Ignoring accessibility requirements",
                "Poor performance on mobile devices",
                "Not handling loading states and error conditions"
            ])
        
        if self._safe_tag_check("backend", context_tags):
            pitfalls.extend([
                "Not handling concurrent access and race conditions",
                "Inadequate input validation and security measures",
                "Poor database query optimization",
                "Not implementing proper logging and monitoring"
            ])
        
        if self._safe_tag_check("security", context_tags):
            pitfalls.extend([
                "Storing sensitive data in plain text",
                "Not validating and sanitizing user inputs",
                "Using weak authentication mechanisms",
                "Exposing sensitive information in error messages"
            ])
        
        return pitfalls
    
    async def _determine_tools_needed(
        self,
        work_item: Dict[str, Any],
        context: PlanningContext
    ) -> List[str]:
        """Determine tools needed for work item execution."""
        tools = context.available_tools.copy() if context.available_tools else []
        
        # Add context-specific tools
        context_tags = work_item.get("context_tags", [])
        item_type = work_item.get("item_type", "task")
        
        # Handle numpy arrays safely
        if hasattr(context_tags, 'tolist'):
            context_tags = context_tags.tolist()
        elif not isinstance(context_tags, list):
            # Safe handling of context_tags to avoid numpy array ambiguity
            try:
                if context_tags is not None:
                    if hasattr(context_tags, 'tolist'):
                        context_tags = context_tags.tolist()
                    context_tags = list(context_tags) if context_tags else []
                else:
                    context_tags = []
            except Exception:
                context_tags = []
        
        # Safe conversion to avoid numpy array boolean evaluation error
        if hasattr(tools, 'tolist'):
            tools = tools.tolist()
        elif not isinstance(tools, list):
            try:
                tools = list(tools) if tools else []
            except Exception:
                tools = []
        
        # Basic development tools
        if len(tools) == 0:
            tools.extend([
                "code_editor",
                "version_control",
                "testing_framework",
                "documentation_tools"
            ])
        
        # Context-specific tools
        if self._safe_tag_check("frontend", context_tags):
            tools.extend([
                "browser_dev_tools",
                "responsive_design_tester",
                "accessibility_checker",
                "performance_profiler"
            ])
        
        if self._safe_tag_check("backend", context_tags):
            tools.extend([
                "api_testing_tool",
                "database_client",
                "performance_monitor",
                "log_analyzer"
            ])
        
        if self._safe_tag_check("database", context_tags):
            tools.extend([
                "database_management_tool",
                "query_optimizer",
                "migration_tool",
                "backup_tool"
            ])
        
        # Remove duplicates and return
        return list(set(tools))
    
    async def _load_template(self, template_type: str) -> str:
        """Load prompt template from file or return default."""
        if template_type in self._template_cache:
            return self._template_cache[template_type]
        
        # Try to load from file if prompts directory exists
        if self.prompts_directory and self.prompts_directory.exists():
            template_file = self.prompts_directory / f"{template_type}.md"
            if template_file.exists():
                try:
                    template = template_file.read_text()
                    self._template_cache[template_type] = template
                    return template
                except Exception as e:
                    self.logger.warning(f"Error loading template {template_file}: {str(e)}")
        
        # Return default template
        default_template = await self._get_default_template(template_type)
        self._template_cache[template_type] = default_template
        return default_template
    
    async def _get_default_template(self, template_type: str) -> str:
        """Get default prompt template."""
        templates = {
            "execution": """
You are an expert AI agent tasked with executing the following work item:

**Work Item**: {title}
**Type**: {item_type}
**Priority**: {priority}
**Complexity**: {complexity}

**Description**:
{description}

**Context Tags**: {context_tags}

**Execution Approach**:
{approach}

**Key Considerations**:
{considerations}

**Success Criteria**:
{success_criteria}

**Best Practices to Follow**:
{best_practices}

**Common Pitfalls to Avoid**:
{common_pitfalls}

**Available Tools**: {tools_needed}

**Environment**: {environment}

Please execute this work item following the guidance above. Provide detailed progress updates and ensure all success criteria are met.
""",
            "validation": """
You are an expert AI agent tasked with validating the completion of the following work item:

**Work Item**: {title}
**Acceptance Criterion**: {criterion}

**Implementation Details**:
{implementation_details}

**Validation Instructions**:
1. Review the implementation against the acceptance criterion
2. Test the functionality thoroughly
3. Verify edge cases and error conditions
4. Confirm documentation is updated
5. Provide detailed validation report

Please validate this criterion and provide a comprehensive assessment.
""",
            "planning": """
You are an expert AI agent tasked with planning the execution of the following work item:

**Work Item**: {title}
**Type**: {item_type}
**Complexity**: {complexity}

**Description**:
{description}

**Requirements**:
{requirements}

**Constraints**:
{constraints}

**Planning Instructions**:
1. Analyze the work item requirements and constraints
2. Break down into manageable tasks if needed
3. Identify dependencies and risks
4. Estimate effort and timeline
5. Create detailed execution plan

Please create a comprehensive execution plan for this work item.
"""
        }
        
        return templates.get(template_type, templates["execution"])
    
    async def _generate_template_variables(
        self,
        work_item: Dict[str, Any],
        context: PlanningContext
    ) -> Dict[str, Any]:
        """Generate variables for template rendering."""
        # Generate AI guidance for template variables
        guidance = await self.generate_execution_guidance(
            work_item, context, GuidanceType.TACTICAL
        )
        
        return {
            "title": work_item.get("title", "Untitled Work Item"),
            "item_type": work_item.get("item_type", "task"),
            "priority": work_item.get("priority", "medium"),
            "complexity": work_item.get("complexity", "moderate"),
            "description": work_item.get("description", "No description provided"),
            "context_tags": self._safe_join_tags(work_item.get("context_tags", [])),
            "approach": guidance.approach,
            "considerations": "\n".join(f"- {c}" for c in guidance.key_considerations),
            "success_criteria": "\n".join(f"- {c}" for c in guidance.success_criteria),
            "best_practices": "\n".join(f"- {p}" for p in guidance.best_practices),
            "common_pitfalls": "\n".join(f"- {p}" for p in guidance.common_pitfalls),
            "tools_needed": ", ".join(guidance.tools_needed),
            "environment": getattr(context, 'execution_environment', 'development'),
            "requirements": "\n".join(f"- {c}" for c in work_item.get("acceptance_criteria", [])),
            "constraints": "\n".join(f"- {c}" for c in getattr(context, 'constraints', []))
        }
    
    async def _render_template(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """Render template with variables."""
        try:
            return template.format(**variables)
        except KeyError as e:
            self.logger.warning(f"Missing template variable: {str(e)}")
            # Replace missing variables with placeholder
            for key, value in variables.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
    
    async def _generate_step_instruction(
        self,
        step: ExecutionStep,
        step_number: int,
        detail_level: InstructionDetail,
        execution_plan: ExecutionPlan
    ) -> Dict[str, Any]:
        """Generate instruction for a single execution step."""
        instruction = {
            "step_number": step_number,
            "step_id": step.step_id,
            "title": step.title,
            "description": step.description,
            "priority": step.priority.value,
            "estimated_duration": str(step.estimated_duration) if step.estimated_duration else None
        }
        
        # Handle array-like detail_level safely
        detail_level_value = detail_level
        if hasattr(detail_level, 'item'):
            detail_level_value = detail_level.item()
        elif hasattr(detail_level, '__iter__') and not isinstance(detail_level, str):
            try:
                detail_level_value = next(iter(detail_level))
            except (StopIteration, TypeError):
                detail_level_value = detail_level
        
        # Safe check for detail level to avoid array comparison issues
        try:
            if hasattr(detail_level_value, 'value'):
                detail_check = detail_level_value.value in [InstructionDetail.DETAILED.value, InstructionDetail.COMPREHENSIVE.value]
            else:
                detail_check = str(detail_level_value) in [str(InstructionDetail.DETAILED), str(InstructionDetail.COMPREHENSIVE)]
        except Exception:
            detail_check = False
        
        if detail_check:
            instruction.update({
                "dependencies": step.dependencies,
                "validation_criteria": step.validation_criteria,
                "parallel_eligible": step.parallel_eligible
            })
            
            if step.ai_guidance:
                instruction["ai_guidance"] = {
                    "approach": step.ai_guidance.approach,
                    "key_considerations": step.ai_guidance.key_considerations,
                    "success_criteria": step.ai_guidance.success_criteria
                }
        
        if detail_level == InstructionDetail.COMPREHENSIVE:
            if step.ai_guidance:
                instruction["ai_guidance"].update({
                    "best_practices": step.ai_guidance.best_practices,
                    "common_pitfalls": step.ai_guidance.common_pitfalls,
                    "tools_needed": step.ai_guidance.tools_needed
                })
            
            # Add context from execution plan
            if execution_plan.critical_path and step.step_id in execution_plan.critical_path.path_steps:
                instruction["on_critical_path"] = True
            
            if execution_plan.risk_assessment:
                step_risks = [
                    risk for risk in execution_plan.risk_assessment.risk_factors
                    if step.step_id in risk.affected_steps
                ]
                # Safely convert to Python list to avoid NumPy array boolean evaluation error
                try:
                    if hasattr(step_risks, 'tolist'):
                        step_risks = step_risks.tolist()
                    elif not isinstance(step_risks, list):
                        step_risks = list(step_risks)
                except Exception:
                    step_risks = list(step_risks) if step_risks is not None else []
                
                if len(step_risks) > 0:
                    instruction["risks"] = [
                        {
                            "description": risk.description,
                            "impact": risk.impact.value,
                            "mitigation_strategies": risk.mitigation_strategies
                        }
                        for risk in step_risks
                    ]
        
        return instruction
    
    async def _generate_validation_prompt(
        self,
        work_item: Dict[str, Any],
        criterion: str
    ) -> str:
        """Generate validation prompt for acceptance criterion."""
        template = await self._load_template("validation")
        
        variables = {
            "title": work_item.get("title", "Untitled Work Item"),
            "criterion": criterion,
            "implementation_details": "[Implementation details to be provided]"
        }
        
        return await self._render_template(template, variables)
    
    def _safe_join_tags(self, tags: Any) -> str:
        """Safely convert tags to a comma-separated string."""
        if tags is None:
            return ""
        
        # Handle different tag formats
        if isinstance(tags, str):
            return tags
        elif isinstance(tags, list):
            return ", ".join(str(tag) for tag in tags)
        elif hasattr(tags, 'tolist'):
            # Handle numpy arrays or similar
            try:
                return ", ".join(str(tag) for tag in tags.tolist())
            except Exception:
                return str(tags)
        else:
            # Fallback for other types
            try:
                return ", ".join(str(tag) for tag in list(tags))
            except Exception:
                return str(tags)
    
    def _safe_tag_check(self, tag: str, context_tags: Any) -> bool:
        """Safely check if a tag is in context_tags, handling arrays."""
        try:
            if context_tags is None:
                return False
            
            # Handle numpy arrays
            if hasattr(context_tags, 'tolist'):
                context_tags = context_tags.tolist()
            
            # Handle string representation of lists - safe check for numpy arrays
            if isinstance(context_tags, str):
                try:
                    if context_tags.startswith('[') and context_tags.endswith(']'):
                        try:
                            import ast
                            context_tags = ast.literal_eval(context_tags)
                        except (ValueError, SyntaxError):
                            return tag in context_tags
                    else:
                        return tag in context_tags
                except Exception:
                    return False
            
            # Handle iterables - safe conversion to avoid numpy array ambiguity
            if hasattr(context_tags, '__iter__'):
                try:
                    # Convert to list safely to avoid numpy array boolean evaluation
                    tags_list = list(context_tags) if context_tags else []
                    return tag in tags_list
                except Exception:
                    return False
            else:
                return tag == str(context_tags)
        except Exception:
            return False
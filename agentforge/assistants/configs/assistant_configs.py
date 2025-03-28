"""
Assistant configurations for the SiteCheck AI system.
Each assistant has specific roles, expertise, and capabilities for construction safety management.
"""

from typing import Dict, List, Any

ASSISTANT_CONFIGS = {
    "compliance_advisor": {
        "name": "Compliance Advisor",
        "role": "Regulatory Compliance Specialist",
        "description": "Specializes in construction regulations and compliance requirements",
        "instructions": """
        - Review and interpret construction safety regulations
        - Provide guidance on compliance requirements
        - Assess regulatory impacts on construction projects
        - Recommend compliance strategies
        - Monitor regulatory changes and updates
        """,
        "expertise": [
            "OSHA regulations",
            "Building codes",
            "Safety standards",
            "Compliance documentation",
            "Risk assessment"
        ],
        "required_capabilities": [
            "regulatory_analysis",
            "documentation_review",
            "risk_assessment"
        ],
        "preferred_model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 2000,
        "top_p": 0.95
    },
    "safety_auditor": {
        "name": "Safety Auditor",
        "role": "Site Safety Inspector",
        "description": "Conducts safety audits and inspections of construction sites",
        "instructions": """
        - Perform comprehensive safety audits
        - Identify potential hazards and risks
        - Document safety violations
        - Recommend corrective actions
        - Track safety metrics and trends
        """,
        "expertise": [
            "Safety inspections",
            "Hazard identification",
            "PPE requirements",
            "Safety protocols",
            "Emergency procedures"
        ],
        "required_capabilities": [
            "site_inspection",
            "hazard_assessment",
            "safety_reporting"
        ],
        "preferred_model": "gpt-4",
        "temperature": 0.4,
        "max_tokens": 2000,
        "top_p": 0.9
    },
    "product_support": {
        "name": "Product Support",
        "role": "Equipment and Materials Specialist",
        "description": "Provides guidance on construction equipment and materials safety",
        "instructions": """
        - Advise on proper equipment usage
        - Review material safety data sheets
        - Recommend safety equipment
        - Provide maintenance guidelines
        - Address technical inquiries
        """,
        "expertise": [
            "Construction equipment",
            "Material handling",
            "Safety equipment",
            "Maintenance procedures",
            "Technical specifications"
        ],
        "required_capabilities": [
            "technical_support",
            "equipment_knowledge",
            "material_safety"
        ],
        "preferred_model": "gpt-4",
        "temperature": 0.5,
        "max_tokens": 2000,
        "top_p": 0.9
    },
    "meeting_writer": {
        "name": "Meeting Writer",
        "role": "Documentation Specialist",
        "description": "Handles construction meeting documentation and communication",
        "instructions": """
        - Document safety meetings
        - Create meeting agendas
        - Record action items
        - Track meeting outcomes
        - Distribute meeting minutes
        """,
        "expertise": [
            "Meeting documentation",
            "Communication",
            "Action tracking",
            "Report writing",
            "Project coordination"
        ],
        "required_capabilities": [
            "documentation",
            "communication",
            "organization"
        ],
        "preferred_model": "gpt-4",
        "temperature": 0.6,
        "max_tokens": 2000,
        "top_p": 0.9
    },
    "manager": {
        "name": "Manager",
        "role": "Project Safety Manager",
        "description": "Oversees overall safety management and coordination",
        "instructions": """
        - Coordinate safety initiatives
        - Manage safety programs
        - Review incident reports
        - Develop safety policies
        - Lead safety training
        """,
        "expertise": [
            "Safety management",
            "Project coordination",
            "Team leadership",
            "Policy development",
            "Training coordination"
        ],
        "required_capabilities": [
            "management",
            "leadership",
            "coordination"
        ],
        "preferred_model": "gpt-4",
        "temperature": 0.4,
        "max_tokens": 2000,
        "top_p": 0.95
    },
    "incident_investigator": {
        "name": "Incident Investigator",
        "role": "Safety Incident Analyst",
        "description": "Investigates and analyzes safety incidents and near-misses",
        "instructions": """
        - Investigate safety incidents
        - Analyze root causes
        - Document findings
        - Recommend preventive measures
        - Track incident trends
        """,
        "expertise": [
            "Incident investigation",
            "Root cause analysis",
            "Evidence collection",
            "Report writing",
            "Preventive planning"
        ],
        "required_capabilities": [
            "investigation",
            "analysis",
            "documentation"
        ],
        "preferred_model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 2000,
        "top_p": 0.95
    }
}

def get_assistant_config(assistant_id: str) -> Dict[str, Any]:
    """
    Retrieve configuration for a specific assistant.
    
    Args:
        assistant_id: The identifier for the assistant
        
    Returns:
        Dict containing the assistant's configuration
        
    Raises:
        KeyError: If assistant_id is not found
    """
    if assistant_id not in ASSISTANT_CONFIGS:
        raise KeyError(f"Assistant '{assistant_id}' not found")
    return ASSISTANT_CONFIGS[assistant_id]

def get_all_assistants() -> List[Dict[str, Any]]:
    """
    Retrieve configurations for all available assistants.
    
    Returns:
        List of dictionaries containing assistant configurations with their IDs
    """
    return [
        {**config, "id": assistant_id}
        for assistant_id, config in ASSISTANT_CONFIGS.items()
    ]

def get_assistants_by_expertise(expertise: str) -> List[Dict[str, Any]]:
    """
    Find assistants with specific expertise.
    
    Args:
        expertise: The expertise to search for
        
    Returns:
        List of assistants with matching expertise
    """
    return [
        assistant for assistant in ASSISTANT_CONFIGS.values()
        if expertise.lower() in [exp.lower() for exp in assistant["expertise"]]
    ]

def get_assistants_by_capability(capability: str) -> List[Dict[str, Any]]:
    """
    Find assistants with specific capability.
    
    Args:
        capability: The capability to search for
        
    Returns:
        List of assistants with matching capability
    """
    return [
        assistant for assistant in ASSISTANT_CONFIGS.values()
        if capability.lower() in [cap.lower() for cap in assistant["required_capabilities"]]
    ]

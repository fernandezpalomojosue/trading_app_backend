# app/domain/services/strategy_validator.py
"""
DSL Validator

Pure function layer for validating Trading Strategy DSL.
Stateless, deterministic, testable - no dependencies on DB or services.

Validates:
- AST structure validity
- Operators against registry
- Node correctness
- Depth limit (prevents infinite trees from AI generation)
- NOT rules (exactly 1 valid child)
- DSL root normalization
- DSL version
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from app.domain.entities.strategy_dsl import (
    StrategyDSL, Node, Expression,
    AndNode, OrNode, NotNode, Condition,
    Constant, Price, Indicator
)
from app.domain.services.strategy_registry import StrategyRegistry


@dataclass
class ValidationResult:
    """Result of DSL validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    depth: int = 0
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class DSLValidator:
    """
    Validator for Trading Strategy DSL.
    
    Pure function layer - no side effects, no DB dependencies.
    Can be used to validate DSL before persistence or for preview.
    """
    
    # Maximum allowed depth for AST (prevents AI-generated infinite trees)
    MAX_DEPTH: int = 10
    
    @classmethod
    def validate(cls, dsl: StrategyDSL) -> ValidationResult:
        """
        Validate a complete StrategyDSL object.
        
        Returns ValidationResult with errors, warnings, and depth.
        """
        errors = []
        warnings = []
        
        # Validate version
        if dsl.version < 1:
            errors.append(f"DSL version must be >= 1, got {dsl.version}")
        
        # Validate root exists
        if dsl.root is None:
            errors.append("Root node cannot be None")
            return ValidationResult(is_valid=False, errors=errors, depth=0)
        
        # Validate root is a valid node
        root_errors = cls._validate_root_node(dsl.root)
        errors.extend(root_errors)
        
        # Validate AST structure and calculate depth
        depth, ast_errors, ast_warnings = cls._validate_node(dsl.root, current_depth=1)
        errors.extend(ast_errors)
        warnings.extend(ast_warnings)
        
        # Check depth limit
        if depth > cls.MAX_DEPTH:
            errors.append(f"AST depth ({depth}) exceeds maximum allowed ({cls.MAX_DEPTH})")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            depth=depth
        )
    
    @classmethod
    def _validate_root_node(cls, root: Node) -> List[str]:
        """Validate root node normalization rules"""
        errors = []
        
        # Root cannot be null (already checked, but defensive)
        if root is None:
            errors.append("Root node cannot be None")
            return errors
        
        # Root cannot be an orphan condition without logical context
        # Conditions should be wrapped in logical nodes at root level
        if isinstance(root, Condition):
            # This is allowed but we warn about it
            pass  # Single condition as root is technically valid
        
        return errors
    
    @classmethod
    def _validate_node(
        cls,
        node: Union[Node, Expression],
        current_depth: int = 1
    ) -> tuple[int, List[str], List[str]]:
        """
        Recursively validate a node and calculate its depth.
        
        Returns: (depth, errors, warnings)
        """
        errors = []
        warnings = []
        max_child_depth = current_depth
        
        # Check depth limit early
        if current_depth > cls.MAX_DEPTH:
            return current_depth, [f"Node at depth {current_depth} exceeds maximum depth"], []
        
        # Handle logical nodes
        if isinstance(node, AndNode):
            # Validate children count
            if len(node.children) < 2:
                errors.append(f"AND node must have at least 2 children, got {len(node.children)}")
            if len(node.children) > 10:
                warnings.append(f"AND node has {len(node.children)} children, consider simplifying")
            
            # Recursively validate children
            for i, child in enumerate(node.children):
                child_depth, child_errors, child_warnings = cls._validate_node(child, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)
                errors.extend([f"AND child[{i}]: {e}" for e in child_errors])
                warnings.extend([f"AND child[{i}]: {w}" for w in child_warnings])
        
        elif isinstance(node, OrNode):
            # Validate children count
            if len(node.children) < 2:
                errors.append(f"OR node must have at least 2 children, got {len(node.children)}")
            if len(node.children) > 10:
                warnings.append(f"OR node has {len(node.children)} children, consider simplifying")
            
            # Recursively validate children
            for i, child in enumerate(node.children):
                child_depth, child_errors, child_warnings = cls._validate_node(child, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)
                errors.extend([f"OR child[{i}]: {e}" for e in child_errors])
                warnings.extend([f"OR child[{i}]: {w}" for w in child_warnings])
        
        elif isinstance(node, NotNode):
            # Validate NOT has exactly 1 valid child
            if node.child is None:
                errors.append("NOT node child cannot be None")
            else:
                # Validate child is not a list (common AI mistake)
                if isinstance(node.child, list):
                    errors.append("NOT node child cannot be a list, must be a single node")
                else:
                    child_depth, child_errors, child_warnings = cls._validate_node(node.child, current_depth + 1)
                    max_child_depth = max(max_child_depth, child_depth)
                    errors.extend([f"NOT child: {e}" for e in child_errors])
                    warnings.extend([f"NOT child: {w}" for w in child_warnings])
        
        elif isinstance(node, Condition):
            # Validate condition
            cond_errors, cond_warnings = cls._validate_condition(node)
            errors.extend(cond_errors)
            warnings.extend(cond_warnings)
        
        elif isinstance(node, Expression):
            # Expressions are leaf nodes, validate directly
            expr_errors = cls._validate_expression(node)
            errors.extend(expr_errors)
        
        else:
            errors.append(f"Unknown node type: {type(node).__name__}")
        
        return max_child_depth, errors, warnings
    
    @classmethod
    def _validate_condition(cls, condition: Condition) -> tuple[List[str], List[str]]:
        """Validate a condition node"""
        errors = []
        warnings = []
        
        # Validate operator
        if not StrategyRegistry.is_valid_operator(condition.operator):
            errors.append(f"Unknown operator: {condition.operator}")
            valid_ops = StrategyRegistry.get_all_operators()
            errors.append(f"Valid operators are: {', '.join(valid_ops)}")
        
        # Validate left and right expressions
        left_errors = cls._validate_expression(condition.left)
        right_errors = cls._validate_expression(condition.right)
        
        errors.extend([f"left: {e}" for e in left_errors])
        errors.extend([f"right: {e}" for e in right_errors])
        
        return errors, warnings
    
    @classmethod
    def _validate_expression(cls, expression: Expression) -> List[str]:
        """Validate an expression (constant, price, indicator)"""
        errors = []
        
        if isinstance(expression, Constant):
            # Constants are always valid
            pass
        
        elif isinstance(expression, Price):
            # Validate price field
            if not StrategyRegistry.is_valid_price_field(expression.field):
                errors.append(f"Unknown price field: {expression.field}")
                valid_fields = StrategyRegistry.PRICE_FIELDS
                errors.append(f"Valid price fields are: {', '.join(sorted(valid_fields))}")
        
        elif isinstance(expression, Indicator):
            # Validate indicator name
            if not StrategyRegistry.is_valid_indicator(expression.name):
                errors.append(f"Unknown indicator: {expression.name}")
                valid_indicators = StrategyRegistry.get_all_indicators()
                errors.append(f"Valid indicators are: {', '.join(valid_indicators)}")
            else:
                # Validate indicator parameters
                param_errors = StrategyRegistry.validate_indicator_params(
                    expression.name, 
                    expression.params
                )
                errors.extend(param_errors)
        
        else:
            errors.append(f"Unknown expression type: {type(expression).__name__}")
        
        return errors
    
    @classmethod
    def validate_json(cls, dsl_json: Dict[str, Any]) -> ValidationResult:
        """
        Validate raw JSON without parsing to StrategyDSL first.
        
        Useful for quick validation before full parsing.
        """
        errors = []
        
        # Check version field
        if "version" not in dsl_json:
            errors.append("Missing required field: 'version'")
        elif not isinstance(dsl_json.get("version"), int) or dsl_json.get("version") < 1:
            errors.append("Field 'version' must be a positive integer")
        
        # Check root field
        if "root" not in dsl_json:
            errors.append("Missing required field: 'root'")
        elif dsl_json.get("root") is None:
            errors.append("Field 'root' cannot be null")
        elif not isinstance(dsl_json.get("root"), dict):
            errors.append("Field 'root' must be an object")
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors, depth=0)
        
        # Parse and validate
        try:
            dsl = StrategyDSL.model_validate(dsl_json)
            return cls.validate(dsl)
        except Exception as e:
            errors.append(f"Failed to parse DSL: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors, depth=0)
    
    # Alias for backward compatibility with tests
    validate_from_json = validate_json

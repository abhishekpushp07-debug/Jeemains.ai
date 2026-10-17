"""
A04 AUDIT: Unknown audience fails open
SCOPE: Isolated test using validation logic
RULE: content.py create/publish should reject unknown audience values,
      permitted() should fail closed for unknown values

HYPOTHESIS: Setting audience='private-typo' passes validation and
            permitted() returns True (fails open instead of closed).
            
ISOLATION: Direct function testing, no database writes
"""
import asyncio
import sys
import os
sys.path.insert(0, '/app/backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from tejas.content import permitted

async def test_unknown_audience():
    """Test if unknown audience values fail open in permitted()"""
    
    print("Testing permitted() function with various audience values:")
    print()
    
    # Test case 1: Valid audience='all'
    set_all = {
        "audience": "all",
        "expires": None,
    }
    result_all = permitted(set_all, None)
    print(f"✓ audience='all': permitted() = {result_all} (expected: True)")
    
    # Test case 2: Valid audience='restricted' with matching user
    set_restricted = {
        "audience": "restricted",
        "allowed_emails": ["test@example.com"],
        "allowed_phones": ["+919876543210"],
        "expires": None,
    }
    user_match = {"email": "test@example.com", "phone": None}
    result_restricted_match = permitted(set_restricted, user_match)
    print(f"✓ audience='restricted' (user matches): permitted() = {result_restricted_match} (expected: True)")
    
    # Test case 3: Valid audience='restricted' with non-matching user
    user_no_match = {"email": "other@example.com", "phone": None}
    result_restricted_no_match = permitted(set_restricted, user_no_match)
    print(f"✓ audience='restricted' (user doesn't match): permitted() = {result_restricted_no_match} (expected: False)")
    
    # Test case 4: VULNERABILITY - Unknown audience value
    set_typo = {
        "audience": "private-typo",  # Invalid value
        "expires": None,
    }
    result_typo = permitted(set_typo, None)
    print(f"\n⚠ audience='private-typo': permitted() = {result_typo}")
    
    # Test case 5: Another unknown value
    set_internal = {
        "audience": "internal",  # Not in validation
        "expires": None,
    }
    result_internal = permitted(set_internal, None)
    print(f"⚠ audience='internal': permitted() = {result_internal}")
    
    # Test case 6: Empty string
    set_empty = {
        "audience": "",
        "expires": None,
    }
    result_empty = permitted(set_empty, None)
    print(f"⚠ audience='': permitted() = {result_empty}")
    
    # Analyze results
    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("=" * 80)
    
    # Check permitted() implementation (lines 84-98 in content.py)
    print("\nCode analysis of permitted() function:")
    print("  Line 86-88: Checks if expires is in the past")
    print("  Line 89: Checks if audience == 'restricted'")
    print("  Line 90-97: If restricted, checks user email/phone")
    print("  Line 98: Returns True for ALL other cases")
    print()
    
    if result_typo and result_internal and result_empty:
        print("⚠ VULNERABILITY CONFIRMED:")
        print("  - audience='private-typo' returns True (fails open)")
        print("  - audience='internal' returns True (fails open)")
        print("  - audience='' returns True (fails open)")
        print("  - Only 'restricted' is checked; all other values default to True")
        print()
        print("✓ AUDIT FINDING: content.py lines 84-98 (permitted function)")
        print("  Function only checks for audience=='restricted'")
        print("  All unknown values fail open (return True)")
        print("  Should fail closed (return False) for unknown values")
        print()
        
        # Check validation in create_set and update_set
        print("Additional finding:")
        print("  - create_set (line 159): No audience validation")
        print("  - update_set (line 210-213): Only checks 'all' or 'restricted'")
        print("  - SetInput model (line 29): audience is plain str, no enum")
        print("  - Invalid values pass validation and persist to database")
        print()
        
        # Test what happens on publish
        print("Impact on publish:")
        print("  - publish() (line 606-607) checks qa_only + restricted")
        print("  - Does NOT validate audience field itself")
        print("  - Invalid audience can be published")
        print("  - set_detail() (line 144) uses permitted() -> fails open")
        print("  - Catalog excludes published sets, but direct access permits")
        
        return True
    else:
        print("✗ Expected all unknown values to return True, but got:")
        print(f"  private-typo: {result_typo}")
        print(f"  internal: {result_internal}")
        print(f"  empty: {result_empty}")
        return False

async def test_validation_bypass():
    """Test if invalid audience passes create/update validation"""
    
    print("\n" + "=" * 80)
    print("Testing validation bypass:")
    print("=" * 80)
    print()
    
    # Simulate SetInput validation
    from pydantic import ValidationError
    from tejas.content import SetInput
    
    try:
        # This should ideally fail but won't because audience is str, not enum
        invalid_input = SetInput(
            title="Test Set",
            exam="JEE Main",
            audience="private-typo",  # Invalid value
            rights_upload=True,
            rights_publish=True,
            rights_report=True,
        )
        print(f"✓ SetInput accepted audience='private-typo'")
        print(f"  Validation passed: {invalid_input.audience}")
        print()
        print("⚠ VULNERABILITY: No enum validation on audience field")
        print("  SetInput model (line 29) uses str instead of Literal['all', 'restricted']")
        return True
        
    except ValidationError as e:
        print(f"✗ Validation rejected invalid audience (unexpected)")
        print(f"  Error: {e}")
        return False

async def main():
    print("=" * 80)
    print("A04 AUDIT: Unknown Audience Fails Open")
    print("=" * 80)
    print("Testing: content.py permitted() and validation")
    print("Isolation: Direct function testing, no database")
    print("=" * 80)
    print()
    
    result1 = await test_unknown_audience()
    result2 = await test_validation_bypass()
    
    print("\n" + "=" * 80)
    if result1 and result2:
        print("RESULT: CONFIRMED - Unknown audience values fail open")
        print("IMPACT: Invalid audience passes validation and permits access")
        print("LOCATION: content.py lines 29 (SetInput), 84-98 (permitted)")
    else:
        print("RESULT: NOT REPRODUCED or TEST ERROR")
    print("=" * 80)
    
    return 0 if (result1 and result2) else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

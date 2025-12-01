"""
Utility functions for parsing the summary into structured data.
"""
import re

def parse_summary_to_structured_data(summary_text: str) -> dict:
    """
    Parse the markdown summary into structured data for the frontend.
    Returns a dictionary with days, ingredients, and recipes.
    """
    result = {
        "days": [],
        "ingredients_by_day": [],
        "recipes_by_day": []
    }
    
    if not summary_text:
        return result
    
    lines = summary_text.split('\n')
    all_days = {}
    current_day = None
    current_section = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Match "DAY 1 (12-23-2025, Tuesday):" - note: no # symbol
        day_match = re.match(r'DAY\s+#?(\d+)\s*\(([^)]+)\):', line, re.IGNORECASE)
        if day_match:
            day_num = int(day_match.group(1))
            day_info = day_match.group(2)
            
            if day_num not in all_days:
                all_days[day_num] = {
                    "day_number": day_num,
                    "day_info": day_info,
                    "meals": {},
                    "ingredients": [],
                    "recipes": []
                }
            current_day = day_num
            current_section = "meals"
            i += 1
            continue
        
        # Match "BREAKFAST: [Recipe Title](URL)"
        meal_match = re.match(r'(BREAKFAST|LUNCH|DINNER):\s*\[([^\]]+)\]\(([^)]+)\)', line, re.IGNORECASE)
        if meal_match and current_day:
            meal_type = meal_match.group(1).lower()
            recipe_title = meal_match.group(2)
            recipe_url = meal_match.group(3)
            
            all_days[current_day]["meals"][meal_type] = {
                "title": recipe_title,
                "url": recipe_url
            }
            
            # Also add to recipes list if not already there
            if not any(r["title"] == recipe_title for r in all_days[current_day]["recipes"]):
                all_days[current_day]["recipes"].append({
                    "title": recipe_title,
                    "url": recipe_url
                })
            i += 1
            continue
        
        # Match "DAY 1 INGREDIENTS:" - note: no # symbol
        ingredients_header = re.match(r'DAY\s+#?(\d+)\s+INGREDIENTS:', line, re.IGNORECASE)
        if ingredients_header:
            current_day = int(ingredients_header.group(1))
            if current_day not in all_days:
                all_days[current_day] = {
                    "day_number": current_day,
                    "day_info": "",
                    "meals": {},
                    "ingredients": [],
                    "recipes": []
                }
            current_section = "ingredients"
            i += 1
            continue
        
        # Match ingredient items (lines starting with -)
        if current_section == "ingredients" and line.startswith('-') and current_day:
            ingredient = line[1:].strip()
            if ingredient:
                all_days[current_day]["ingredients"].append(ingredient)
            i += 1
            continue
        
        # Match "RECIPE LINKS:"
        if re.match(r'RECIPE\s+LINKS:', line, re.IGNORECASE):
            current_section = "recipe_links"
            current_day = None
            i += 1
            continue
        
        # Match "DAY 1:" under recipe links - note: no # symbol
        recipe_day_match = re.match(r'DAY\s+#?(\d+):', line, re.IGNORECASE)
        if recipe_day_match and current_section == "recipe_links":
            current_day = int(recipe_day_match.group(1))
            if current_day not in all_days:
                all_days[current_day] = {
                    "day_number": current_day,
                    "day_info": "",
                    "meals": {},
                    "ingredients": [],
                    "recipes": []
                }
            i += 1
            continue
        
        # Match recipe links "- [Title](URL)"
        recipe_link_match = re.match(r'-\s*\[([^\]]+)\]\(([^)]+)\)', line)
        if recipe_link_match and current_section == "recipe_links" and current_day:
            recipe_title = recipe_link_match.group(1)
            recipe_url = recipe_link_match.group(2)
            
            # Add to recipes if not already there
            if not any(r["title"] == recipe_title for r in all_days[current_day]["recipes"]):
                all_days[current_day]["recipes"].append({
                    "title": recipe_title,
                    "url": recipe_url
                })
            i += 1
            continue
        
        i += 1
    
    # Convert to sorted lists
    result["days"] = [all_days[day_num] for day_num in sorted(all_days.keys())]
    
    # Create ingredients_by_day
    for day_num in sorted(all_days.keys()):
        if all_days[day_num]["ingredients"]:
            result["ingredients_by_day"].append({
                "day_number": day_num,
                "ingredients": all_days[day_num]["ingredients"]
            })
    
    # Create recipes_by_day
    for day_num in sorted(all_days.keys()):
        if all_days[day_num]["recipes"]:
            result["recipes_by_day"].append({
                "day_number": day_num,
                "recipes": all_days[day_num]["recipes"]
            })
    
    return result
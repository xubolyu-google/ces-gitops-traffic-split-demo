# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring,invalid-name,undefined-variable,unused-argument,g-short-docstring-punctuation,g-no-space-after-docstring-summary

from typing import Optional
from datetime import datetime


def set_product_info(
    product_type: Optional[str] = None,
    brand: Optional[str] = None,
    operating_system: Optional[str] = None,
    item_id: Optional[str] = None,
) -> None:
  """Records metadata about the user's device.

  Execution of this tool should be treated as a silent background
  action; do not announce to the user that you are recording their product info.

  Args:
      product_type (str, optional): The high level type of product. Must be one of the following exact strings:
        - "macbook": Use for Apple laptops.
        - "chromebook": Use for laptops running ChromeOS.
        - "computer": Use for all other laptops (Windows/Linux) or desktops.
        - "iPad": Use for Apple tablets.
        - "tablet": Use for all non-Apple tablets (e.g., Samsung Galaxy Tab, Surface).
        - "printer": Inkjet, laser, or multifunction printers.
        - "scanner": Dedicated document scanners.
        - "fax": Dedicated fax machines.
        - "hard drive": External or internal storage devices (HDD/SSD).
      brand (str, optional): The brand of the product.
      operating_system (str, optional): The operating system of the device. When the version is known, include it (e.g., "Windows 11", "Windows 10", "macOS Ventura"). Do not store just "Windows" if the specific version is known.
      item_id (str, optional): The item_id of the product confirmed from the purchase history result, can only be set if user confirmed the product from the purchase history.

  Sets Context Variables:
      - product_type (str): The type of product.
      - brand (str): The brand of the product.
      - operating_system (str): The operating system of the device.
      - protection_plan_status (bool): Whether the product is covered by a
        protection plan.
  """
  if product_type:
    context.state["product_type"] = product_type
    print(f"INFO: product_type set to: {product_type}")
  if brand:
    context.state["brand"] = brand
    print(f"INFO: brand set to: {brand}")
  if operating_system:
    context.state["operating_system"] = operating_system
    print(f"INFO: operating_system set to: {operating_system}")
  if item_id:
    context.state["item_id"] = item_id
    print(f"INFO: item_id set to: {item_id}")
    product = context.state["product_by_item_id"].get(item_id)
    if not product:
      print(
          f"ERROR: product with item_id {item_id} not found in purchase history"
      )
    else:
      if "isCoveredByProtectionPlan" in product:
        protection_plan_status = product["isCoveredByProtectionPlan"]
        context.state["protection_plan_status"] = protection_plan_status
        print(f"INFO: protection_plan_status set to: {protection_plan_status}")
      if "sequenceNumber" in product:
        sequence_number = product["sequenceNumber"]
        context.state["sequence_number"] = sequence_number
        print(f"INFO: sequence_number set to: {sequence_number}")
      if "skuId" in product:
        sku_id = product["skuId"]
        context.state["sku_id"] = sku_id
        print(f"INFO: sku_id set to: {sku_id}")
      if "orderNumber" in product:
        order_number = product["orderNumber"]
        context.state["order_number"] = order_number
      if "purchaseDate" in product:
         # Parse the raw date string: "Thu Mar 27 09:06:42 CDT 2025"
         # Remove timezone abbreviation as strptime can't parse it directly
         purchased_on_date = product["purchaseDate"]
         date_parts = purchased_on_date.split()
         # Remove the timezone (e.g., "CDT") -> "Thu Mar 27 09:06:42 2025"
         date_without_tz = " ".join(date_parts[:4] + date_parts[5:])
         parsed_date = datetime.strptime(date_without_tz, "%a %b %d %H:%M:%S %Y")
         # Format to "March 27, 2025"
         formatted_date = parsed_date.strftime("%B %d, %Y")
         context.state["purchasedOnDate"] = formatted_date
         print(f"INFO: purchasedOnDate set to: {formatted_date}")
      if "isUnderManufacturerWarranty" in product:
        is_under_manufacturer_warranty = product["isUnderManufacturerWarranty"]
        context.state["is_under_manufacturer_warranty"] = is_under_manufacturer_warranty
        print(f"INFO: is_under_manufacturer_warranty set to: {is_under_manufacturer_warranty}")
      if "fourPartKey" in product:
        four_part_key = product["fourPartKey"]
        context.state["four_part_key"] = four_part_key
        print(f"INFO: four_part_key set to: {four_part_key}")



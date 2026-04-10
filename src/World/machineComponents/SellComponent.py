from .Component import Component

class SellComponent(Component):
    def __init__(self, name, machine, componentData):
        super().__init__(name, machine, componentData)
        self.updateType = "event"  # Update type for this component is event, meaning it only updates when an event is triggered

    def handleEvent(self, event, eventData, componentName, component):
        """Handle events related to items being sold."""
        if event != "collision": return
        item = eventData.get("item")
        if not item: return
        
        allItemData = self.machine.callData("sprites")
        itemName = allItemData.get(item.name, {})
        itemPrice = itemName["itemData"].get("sell_price", 0)
        price = itemPrice
        self.machine.pushEvent("item_sold", {"item": item, "price": price}, self.name, self)
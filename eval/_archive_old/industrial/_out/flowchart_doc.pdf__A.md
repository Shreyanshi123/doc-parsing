# Order Fulﬁlment Process

The diagram shows how an order moves through the plant.

**Figure (page 1, flowchart)**

Boxes/entities:
- Receive order
- Check stock
- Pack items
- Reorder stock
- Ship
- Send invoice

Connections:
- Receive order -> Check stock
- Check stock -> Pack items
- Check stock -> Reorder stock
- Pack items -> Ship
- Ship -> Send invoice

Figure 1. Order ﬂow.

# Owners

|Step|Owner|
|---|---|
|Receive order|Sales|
|Check stock|Warehouse|
|Ship|Logistics|
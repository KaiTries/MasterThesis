# Draft for the Scenario Protocol

### Context

Based on the simple Buy Protocol we extend the Scenario to achieve more complexity.
In line with the web context and the process of buying things we take inspiration from e-commerce platforms, such as amazon.
When buying a Product we can generally select Delivery options, which hide a lot of possible complexity.
It is also possible to increase complexity by modeling the marketplace aspect of these platforms, where people can resell products.

### Protocol extended Purchase

```
Purchase {
    roles Buyer, Seller, Deliverer
    parameters item, price, buyerAddess, deliveryCost, productInStock, productOutOfStock, decision

    # Buyer puts product in chart <- only works if product still in stock
    Buyer -> Seller: AskForItem(out item, out price)
    Seller -> Buyer: Accept(in item, in price, out productInStock, out decision)
    Seller -> Buyer: Reject(in item, in price, out productOutOfStock, out decision)

    # Buyer informs Seller of its address
    Buyer -> Seller: GiveAdress(out buyerAddress)

    # Seller checks with deliverer what the cost would be
    DeliveryCost(Seller, Deliverer, in buyerAddress, in item, out deliveryCost)

    # Buyer gets informed of cost and decides if he wants delivery or not
    Seller -> Buyer: InformDeliveryPrice(item, )


    #
    Seller -> Deliverer:

    # Seller send final Purchase offer (price (+delveryCost))


}
```

```
DeliveryCost {
    role A, B
    parameters out place, out product, out price

    A -> B: informPlaceProduct(out place, out product)
    B -> A: informOfPrice(in place, in product, out price)
}
```

### Protocol marketplace

```
Purchase {
    role Marketplace, Buyer, Seller

}
```

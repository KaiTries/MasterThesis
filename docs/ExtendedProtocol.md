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
    Seller -> Buyer: InformDeliveryPrice(in item, in deliveryCost)
    Buyer -> Seller: AcceptDelivery(in item, in deliveryCost)
    Buyer -> Seller: RejectDelivery(in item, in deliveryCost)


    # Inform Deliverer that delivery is (not) happening
    Seller -> Deliverer:

    # Buyer actually completes transaction

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
protocol MarketplaceTrade
roles
  B as Buyer,
  M as Marketplace,
  S as Seller

parameters
  key   orderId
  out   listingId, itemId, price, sellerId
  out   buyerId, shipAddr
  out   eta, sellerRef
  out   confirmationId
  out   payToken, receiptId, amount
  out   trackingNo, shipDate
  out   reason, cancelReason

  // Discovery: marketplace informs buyer about a listing
  M -> B: List( out listingId, out itemId, out price, out sellerId )

  // Buyer places an order for the advertised listing
  B -> M: Order ( in listingId, in itemId, in price, in sellerId, out orderId, out buyerId, out shipAddr )

  // Marketplace forwards the order to the seller
  M -> S: ForwardOrder( in  orderId, in  listingId, in itemId, in price, in  buyerId,  in shipAddr )

  // Seller accepts (or rejects) the order
  S -> M: Accept( in  orderId, out eta, out sellerRef )
  S -> M: Reject( in  orderId, out reason )

  // Marketplace confirms acceptance to the buyer
  M -> B: Confirm ( in  orderId, in  eta, out confirmationId )

  // Buyer supplies a payment token to the marketplace
  B -> M: ProvidePayment ( in  orderId, out payToken )

  // Marketplace acknowledges payment capture/authorization
  M -> B: Receipt ( in  orderId, in  payToken, out receiptId, out amount )

  // Seller ships and notifies the marketplace
  S -> M: ShipNotice ( in  orderId, out trackingNo, out shipDate)

  // Marketplace relays shipping details to the buyer
  M -> B: DeliveryUpdate( in  orderId, in  trackingNo, in  shipDate )

  // Optional: buyer cancels before acceptance/fulfillment
  B -> M: Cancel ( in  orderId, out cancelReason )
```

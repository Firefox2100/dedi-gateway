from dedi_gateway.etc.enums import ConnectivityType, TransportType
from dedi_gateway.cache import get_active_cache, get_active_broker
from dedi_gateway.database import get_active_db
from dedi_gateway.model.route import Route
from ..network_message import MessageMetadata, RouteRequest, RouteResponse, RouteNotification
from .network_interface import NetworkInterface


class RouteInterface(NetworkInterface):
    """
    A utility interface to handle route negotiation related operations.
    """
    async def request_route(self,
                            network_id: str,
                            target_node: str,
                            ) -> bool:
        """
        Request a route to a specific node in the network.
        :param network_id: The ID of the network to request the route in.
        :param target_node: The node planning to connect to.
        :return: True if a route was found and established, False otherwise.
        """
        cache = get_active_cache()
        broker = get_active_broker()
        db = get_active_db()
        connected_route = await cache.get_route(target_node)

        if connected_route:
            # Already connected, maybe a race condition
            return True

        network = await db.networks.get(network_id)

        # Send a route request message
        route_request = RouteRequest(
            metadata=MessageMetadata(
                network_id=network_id,
                node_id=network.instance_id,
            ),
            target_node=target_node,
        )

        sent_count = await self.broadcast_message(
            message=route_request,
        )

        responses = [
            r async for r in broker.response_generator(
                message_id=route_request.metadata.message_id,
                message_count=sent_count,
            )
        ]

        # Find the optimal route
        # For now it's the shortest
        # TODO: Implement route and connection scoring
        optimal_route: list[str] | None = None
        for r in responses:
            response_message = RouteResponse.from_dict(r)

            if not response_message.route:
                continue
            if optimal_route is None or len(response_message.route) < len(optimal_route):
                optimal_route = response_message.route

        if optimal_route:
            # Found an optimal route, no need to establish connection, but save it
            initial_route = await cache.get_route(optimal_route[0])

            new_route = Route(
                network_id=network_id,
                node_id=target_node,
                connectivity_type=ConnectivityType.PROXY,
                transport_type=initial_route.transport_type,
                outbound=initial_route.outbound,
                proxy_nodes=optimal_route,
            )
            await cache.save_route(new_route)
            return True

        return False

    async def process_route_request(self,
                                    route_request: RouteRequest,
                                    ):
        """
        Check for available routes to the requested node and respond
        to the route request.
        :param route_request: The route request message containing the target node
        """
        cache = get_active_cache()
        db = get_active_db()

        connected_route = await cache.get_route(route_request.target_node)
        network = await db.networks.get(route_request.metadata.network_id)

        route_response = RouteResponse(
            metadata=MessageMetadata(
                network_id=route_request.metadata.network_id,
                node_id=network.instance_id,
                message_id=route_request.metadata.message_id,
            ),
            target_node=route_request.target_node,
            route=[],
        )

        if connected_route:
            proxy_nodes = [
                network.instance_id,
            ]
            if connected_route.connectivity_type == ConnectivityType.PROXY:
                proxy_nodes.extend(connected_route.proxy_nodes)

            route_response.route = proxy_nodes

        node = await db.nodes.get(route_request.metadata.node_id)

        await self.send_message(
            message=route_response,
            node=node,
        )

    async def notify_route_broken(self,
                                  network_id: str,
                                  broken_node: str,
                                  ):
        """
        Notify the network that a route to a specific node is broken.
        :param network_id: The ID of the network where the route is broken.
        :param broken_node: The node that is no longer reachable.
        """
        db = get_active_db()

        network = await db.networks.get(network_id)

        route_notification = RouteNotification(
            metadata=MessageMetadata(
                network_id=network_id,
                node_id=network.instance_id,
            ),
            target_node=broken_node,
        )

        await self.broadcast_message(
            message=route_notification,
        )

    async def process_route_notification(self,
                                         route_notification: RouteNotification,
                                         ):
        """
        Process a route notification message indicating that a route to a node is broken.
        :param route_notification: The route notification message containing the target node
        """
        cache = get_active_cache()

        connected_route = await cache.get_route(route_notification.target_node)

        if not connected_route:
            # No route to the target node, nothing to do
            return

        if connected_route.connectivity_type == ConnectivityType.PROXY:
            # Remove the route if it was a proxy route
            await cache.delete_route(route_notification.target_node)

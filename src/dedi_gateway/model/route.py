from dedi_gateway.etc.enums import ConnectivityType, TransportType


class Route:
    def __init__(self,
                 network_id: str,
                 node_id: str,
                 connectivity_type: ConnectivityType,
                 transport_type: TransportType,
                 *,
                 outbound: bool = False,
                 proxy_nodes: list = None,
                 websocket = None,
                 sse = None,
                 ):
        """
        A route that defines how data is transferred between this instance and another node in the network.
        :param network_id: The unique ID of the network
        :param node_id: The unique ID of the node to which this route connects
        :param connectivity_type: The type of connectivity for this route (e.g., direct, proxied)
        :param transport_type: The type of transport used for this route (e.g., HTTP, WebSocket)
        :param outbound: Whether this route is initiated by this instance or another node
        :param proxy_nodes: List of nodes that act as proxies for this route, from the closest to the furthest
        :param websocket: Optional WebSocket connection object for this route
        :param sse: Optional Server-Sent Events connection object for this route
        """
        self.network_id = network_id
        self.node_id = node_id
        self.connectivity_type = connectivity_type
        self.transport_type = transport_type
        self.outbound = outbound
        self.proxy_nodes = proxy_nodes or []
        self.websocket = websocket
        self.sse = sse


class RouteRegistry:
    def __init__(self):
        self.routes = {}

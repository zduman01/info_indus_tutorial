import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64


class JointBridge(Node):

    def __init__(self):
        super().__init__('joint_bridge')

        # Mode de fonctionnement : rviz ou gazebo
        self.declare_parameter('mode', 'rviz')
        self.mode = self.get_parameter('mode').value

        if self.mode not in ('rviz', 'gazebo'):
            raise ValueError(f'Mode inconnu : {self.mode}')

        # Coordonnees des articulations issues de Creo (mm)
        self.MG = (-80.0, 70.0)
        self.MD = (58.0, 70.0)

        self.CG = (-80.0, -10.0)
        self.CD = (90.2, -2.1)

        self.P = (19.834, -131.7)

        # Orientations initiales des bras
        self.alpha1 = self.orientation(self.MG, self.CG)
        self.alpha2 = self.orientation(self.CG, self.P)
        self.alpha3 = self.orientation(self.CD, self.P)
        self.alpha4 = self.orientation(self.MD, self.CD)

        # Reception des angles absolus
        self.subscription = self.create_subscription(
            JointState,
            '/pantograph_angles',
            self.callback,
            10
        )

        # Publishers selon le mode de simulation
        if self.mode == 'rviz':

            self.publisher = self.create_publisher(
                JointState,
                '/joint_states',
                10
            )

        elif self.mode == 'gazebo':

            self.pub_gauche = self.create_publisher(
                Float64,
                '/pentographe/moteur_gauche/cmd_pos',
                10
            )

            self.pub_droit = self.create_publisher(
                Float64,
                '/pentographe/moteur_droit/cmd_pos',
                10
            )

        self.get_logger().info(
            f'Joint Bridge demarre en mode {self.mode}'
        )

    @staticmethod
    def orientation(point_a, point_b):
        """Calcule l'orientation d'un segment."""
        return math.atan2(
            point_b[1] - point_a[1],
            point_b[0] - point_a[0]
        )

    @staticmethod
    def normaliser(angle):
        """Ramene un angle entre -pi et pi."""
        return math.atan2(
            math.sin(angle),
            math.cos(angle)
        )

    def convertir_angles(self, angles):
        """Convertit les angles absolus en angles articulaires."""

        # Passage du repere mathematique au repere Creo
        theta1 = -angles['theta1']
        theta2 = -angles['theta2']
        theta3 = -angles['theta3']
        theta4 = -angles['theta4']

        # Angles relatifs des moteurs
        moteur_gauche = self.normaliser(
            self.alpha1 - theta1
        )

        moteur_droit = self.normaliser(
            self.alpha4 - theta4
        )

        # Angles relatifs des coudes
        coude_gauche = self.normaliser(
            self.alpha2 - theta2 - moteur_gauche
        )

        coude_droit = self.normaliser(
            self.alpha3 - theta3 - moteur_droit
        )

        return (
            moteur_gauche,
            coude_gauche,
            moteur_droit,
            coude_droit
        )

    def callback(self, msg):

        angles = dict(zip(msg.name, msg.position))

        noms_requis = [
            'theta1',
            'theta2',
            'theta3',
            'theta4'
        ]

        if not all(nom in angles for nom in noms_requis):
            return

        positions = self.convertir_angles(angles)

        if self.mode == 'rviz':
            self.publier_rviz(positions)

        elif self.mode == 'gazebo':
            self.publier_gazebo(positions)

    def publier_rviz(self, positions):
        """Publie les quatre angles pour RViz."""

        msg = JointState()

        msg.header.stamp = self.get_clock().now().to_msg()

        msg.name = [
            'joint_moteur_gauche',
            'joint_coude_gauche',
            'joint_moteur_droit',
            'joint_coude_droit'
        ]

        msg.position = list(positions)

        self.publisher.publish(msg)

    def publier_gazebo(self, positions):
        """Publie uniquement les angles des moteurs."""

        moteur_gauche = positions[0]
        moteur_droit = positions[2]

        msg_gauche = Float64()
        msg_gauche.data = moteur_gauche

        msg_droit = Float64()
        msg_droit.data = moteur_droit

        self.pub_gauche.publish(msg_gauche)
        self.pub_droit.publish(msg_droit)


def main(args=None):

    rclpy.init(args=args)

    node = JointBridge()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

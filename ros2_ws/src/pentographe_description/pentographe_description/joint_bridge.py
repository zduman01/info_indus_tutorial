import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class JointBridge(Node):

    def __init__(self):
        super().__init__('joint_bridge')

        # Reception des quatre angles absolus d'Andreea
        self.subscription = self.create_subscription(
            JointState,
            '/pantograph_angles',
            self.callback,
            10
        )

        # Publication des angles compatibles avec l'URDF
        self.publisher = self.create_publisher(
            JointState,
            '/joint_states',
            10
        )

        # Coordonnees des points dans Creo (X, Z), en mm
        self.MG = (-80.0, 70.0)
        self.MD = (58.0, 70.0)

        self.CG = (-80.0, -10.0)
        self.CD = (90.2, -2.1)

        self.P = (19.834, -131.7)

        # Orientations initiales des barres dans Creo
        self.alpha1 = math.atan2(
            self.CG[1] - self.MG[1],
            self.CG[0] - self.MG[0]
        )

        self.alpha2 = math.atan2(
            self.P[1] - self.CG[1],
            self.P[0] - self.CG[0]
        )

        self.alpha3 = math.atan2(
            self.P[1] - self.CD[1],
            self.P[0] - self.CD[0]
        )

        self.alpha4 = math.atan2(
            self.CD[1] - self.MD[1],
            self.CD[0] - self.MD[0]
        )

        self.get_logger().info(
            'Joint bridge demarre - 4 angles absolus'
        )

    @staticmethod
    def normaliser(angle):
        return math.atan2(
            math.sin(angle),
            math.cos(angle)
        )

    def callback(self, msg):

        angles = dict(zip(msg.name, msg.position))

        if not all(
            nom in angles
            for nom in ['theta1', 'theta2', 'theta3', 'theta4']
        ):
            return

        theta1 = angles['theta1']
        theta2 = angles['theta2']
        theta3 = angles['theta3']
        theta4 = angles['theta4']

        # Conversion XY mathematique vers XZ Creo
        # Le repere_pen actuel utilise une rotation de -90 deg
        # autour de X : Y mathematique correspond a -Z Creo

        theta1 = -theta1
        theta2 = -theta2
        theta3 = -theta3
        theta4 = -theta4

        # Angles des moteurs
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

        # Message compatible avec l'URDF
        sortie = JointState()

        sortie.header.stamp = self.get_clock().now().to_msg()

        sortie.name = [
            'joint_moteur_gauche',
            'joint_coude_gauche',
            'joint_moteur_droit',
            'joint_coude_droit'
        ]

        sortie.position = [
            moteur_gauche,
            coude_gauche,
            moteur_droit,
            coude_droit
        ]

        self.publisher.publish(sortie)


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

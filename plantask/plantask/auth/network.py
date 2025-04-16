# network.py

TRUSTED_IPS = {"123.45.67.89"}  # Lista de IPs confiables

PING_CODE = "KOCH1234"  # Código de verificación para accesos desde redes no confiables

def is_ip_trusted(ip_address):
    """
    Verifica si una IP está en la lista de IPs confiables.
    """
    return ip_address in TRUSTED_IPS

def is_valid_ping_code(code):
    """
    Verifica si el código Ping ingresado es correcto.
    """
    return code == PING_CODE

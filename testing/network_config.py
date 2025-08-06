"""
Network-aware configuration for adaptive test timeouts
"""
import subprocess
import time

class NetworkConfig:
    """Detect network conditions and provide appropriate timeouts"""
    
    @staticmethod
    def estimate_network_speed():
        """
        Estimate network speed by pinging a reliable server.
        Returns: 'fast', 'normal', or 'slow'
        """
        try:
            # Ping OpenStreetMap tile server
            result = subprocess.run(
                ['ping', '-c', '3', 'tile.openstreetmap.org'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'time=' in result.stdout:
                # Extract average ping time
                times = [float(line.split('time=')[1].split(' ')[0]) 
                        for line in result.stdout.split('\n') 
                        if 'time=' in line]
                avg_ping = sum(times) / len(times) if times else 999
                
                if avg_ping < 50:
                    return 'fast'
                elif avg_ping < 150:
                    return 'normal'
                else:
                    return 'slow'
        except:
            pass
        
        return 'normal'  # Default assumption
    
    @staticmethod
    def get_timeout_multiplier():
        """Get timeout multiplier based on network speed"""
        speed = NetworkConfig.estimate_network_speed()
        return {
            'fast': 0.7,
            'normal': 1.0,
            'slow': 2.0
        }[speed]
    
    @staticmethod
    def get_adaptive_timeout(base_timeout):
        """
        Get adaptive timeout based on current network conditions.
        
        Args:
            base_timeout: Base timeout in seconds
            
        Returns:
            Adjusted timeout based on network speed
        """
        multiplier = NetworkConfig.get_timeout_multiplier()
        return int(base_timeout * multiplier)
    
    @staticmethod
    def log_network_conditions(verbose=False):
        """Log current network conditions for debugging"""
        if verbose:
            speed = NetworkConfig.estimate_network_speed()
            multiplier = NetworkConfig.get_timeout_multiplier()
            print(f"🌐 Network speed: {speed} (timeout multiplier: {multiplier}x)")
            return {'speed': speed, 'multiplier': multiplier}
        return None
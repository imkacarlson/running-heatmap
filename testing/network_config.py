"""
Network-aware configuration for adaptive test timeouts

Optimized for test runtime by eliminating external network dependencies.
Provides consistent 'normal' network assumptions for predictable test timing.
"""

class NetworkConfig:
    """Detect network conditions and provide appropriate timeouts"""
    
    @staticmethod
    def estimate_network_speed():
        """
        Estimate network speed for test optimization.
        
        For test runtime optimization, we assume 'normal' network conditions
        to provide consistent, predictable test timing without external dependencies.
        This eliminates network latency as a variable in test runtime.
        
        Returns: 'normal' (always, for consistent test performance)
        """
        # Return consistent 'normal' speed to eliminate network variables
        # This ensures predictable test timing regardless of actual connectivity
        return 'normal'
    
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
            print(f"🌐 Network speed: {speed} (timeout multiplier: {multiplier}x) - offline test mode")
            return {'speed': speed, 'multiplier': multiplier}
        return None
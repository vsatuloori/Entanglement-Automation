        pso = PSOManager(
            dim=dim,
            bounds=bounds,
            num_particles=num_particles,
            max_iter=max_iter,
            threshold_cost=threshold_cost2
        )

        best_voltage_h, best_cost_h = pso.optimize(
            user_ctrl=Alice.Pol_CTRL1,
            meas_device=Charlie.NIDAQ_USB,
            channels=[2, 1],  # Ch2/Ch1 for visibility calculation
            CostFunction=VisibilityCal,
            MeasureFunction=MeasureFunction
        )
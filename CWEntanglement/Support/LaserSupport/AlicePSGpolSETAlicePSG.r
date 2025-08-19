# Alice.PSG.polSET(Alice.PSG.H)


        # # Step 2: Optimize Charlie.Pol_CTRL1 to minimize Ch2/Ch1 visibility
        # # Initialize the PSO Manager
        # pso = PSOManager(
        #     dim=dim,
        #     bounds=bounds,
        #     num_particles=num_particles,
        #     max_iter=max_iter,
        #     threshold_cost=threshold_cost1
        # )
        
        # best_voltage_charlie_1, best_cost_charlie_1 = pso.optimize(
        #     user_ctrl=Charlie.Pol_CTRL1,
        #     meas_device=Charlie.NIDAQ_USB,
        #     channels=[2, 1],
        #     CostFunction=VisibilityCal,
        #     MeasureFunction=MeasureFunction
        # )

        # print(f"Optimal Voltage for Charlie.Pol_CTRL1 (Ch2/Ch1): {best_voltage_charlie_1}")
        # print(f"Minimum Visibility (Ch2/Ch1): {best_cost_charlie_1}")

        # for i in range(10):
        #     Charlie.Pol_CTRL1.Vset(best_voltage_charlie_1)
        #     measure = MeasureFunction(Charlie.NIDAQ_USB, [2,1])
        #     print(f"i:{i}, visibility:{VisibilityCal(measure)}")
        #     time.sleep(1)

        # # Step 3: Set Alice's PSG to D
        # Alice.PSG.polSET(Alice.PSG.D)

        # # Step 4: Optimize Charlie.Pol_CTRL2 to minimize Ch4/Ch3 visibility
        # # Initialize the PSO Manager
        # pso = PSOManager(
        #     dim=dim,
        #     bounds=bounds,
        #     num_particles=num_particles,
        #     max_iter=max_iter,
        #     threshold_cost=threshold_cost2
        # )

        # best_voltage_charlie_2, best_cost_charlie_2 = pso.optimize(
        #     user_ctrl=Charlie.Pol_CTRL2,
        #     meas_device=Charlie.NIDAQ_USB,
        #     channels=[4,3],
        #     CostFunction=VisibilityCal,
        #     MeasureFunction=MeasureFunction
        # )

        # print(f"Optimal Voltage for Charlie.Pol_CTRL2 (Ch4/Ch3): {best_voltage_charlie_2}")
        # print(f"Minimum Visibility (Ch4/Ch3): {best_cost_charlie_2}")
        
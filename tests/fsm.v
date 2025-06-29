module fsm_example (
    input clk,
    input rst,
    input in,
    output reg [1:0] state
);
    parameter IDLE = 2'b00, S1 = 2'b01, S2 = 2'b10;

    always @(posedge clk or posedge rst) begin
        if (rst)
            state <= IDLE;
        else begin
            case (state)
                IDLE: if (in) state <= S1;
                S1:   if (!in) state <= S2;
                S2:   state <= IDLE;
            endcase
        end
    end
endmodule


// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module fsm_example_tb;
    reg clk;
    reg rst;
  reg in;
  wire [1:0] state;

    fsm_example uut (
        .clk(clk),
        .rst(rst),
        .in(in),
        .state(state)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    initial begin
        rst = 1;
        #10;
        rst = 0;
    end

    initial begin
        in = 0;
        #10;
        in = 0;
        #10;
        in = 1;
        #10;
        $finish;
    end
endmodule
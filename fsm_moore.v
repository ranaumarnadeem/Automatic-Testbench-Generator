module fsm_moore (
    input clk, rst, in,
    output reg [1:0] state,
    output reg out
);
    parameter S0 = 2'b00, S1 = 2'b01, S2 = 2'b10;
    
    always @(posedge clk or posedge rst) begin
        if (rst)
            state <= S0;
        else begin
            case (state)
                S0: state <= in ? S1 : S0;
                S1: state <= in ? S2 : S0;
                S2: state <= S0;
            endcase
        end
    end

    always @(*) begin
        case (state)
            S0: out = 0;
            S1: out = 0;
            S2: out = 1;
        endcase
    end
endmodule


// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module fsm_moore_tb;
    // regs for inputs, wires for outputs
    reg clk;
    reg rst;
  reg in;
  wire [1:0] state;
  wire out;

    fsm_moore uut (
        .clk(clk),
        .rst(rst),
        .in(in),
        .state(state),
        .out(out)
    );

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

    // Reset sequence
    initial begin
        rst = 1; #10; rst = 0;
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

// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module fsm_moore_tb_tb;

    fsm_moore_tb uut (

    );

    initial begin
        #10;
        #10;
        $finish;
    end
endmodule